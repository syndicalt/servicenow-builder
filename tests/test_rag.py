import pytest

from jedi_devproject.rag import (
    Document,
    PublicWebAccessConfig,
    PublicWebResponse,
    PublicWebRetrievalBlocked,
    PublicWebRetriever,
    RagDomain,
    RetrievalBlocked,
    SpecializedRags,
    cache_key,
)


def _rags() -> SpecializedRags:
    return SpecializedRags.from_documents(
        [
            Document(
                domain=RagDomain.SERVICENOW_PLATFORM,
                source="servicenow-docs/update-sets",
                content="Update sets capture portal configuration changes for review.",
                version="washington",
            ),
            Document(
                domain=RagDomain.INSTANCE_METADATA,
                source="instance/sys_dictionary/sp_instance",
                content="sp_instance contains portal widget instance configuration.",
                version="dev-snapshot-1",
            ),
            Document(
                domain=RagDomain.PROJECT_CONTEXT,
                source="project/epic-1",
                content="Portal content changes are in scope for the MVP.",
                version="sprint-1",
            ),
            Document(
                domain=RagDomain.COMPLIANCE,
                source="policy/model-use",
                content="Portal work must not use public AI endpoints unless explicitly approved.",
                version="2026-05",
            ),
        ]
    )


def test_each_specialized_rag_returns_citations() -> None:
    rags = _rags()

    for domain in RagDomain:
        if domain is RagDomain.PUBLIC_DOCUMENTATION:
            continue
        results = rags.retrieve(domain, "portal")
        assert results
        assert results[0].citation.source
        assert results[0].citation.content_hash
        assert 0 <= results[0].citation.confidence <= 1


def test_missing_compliance_context_blocks_candidate_generation() -> None:
    rags = SpecializedRags.from_documents(
        [
            Document(
                domain=RagDomain.SERVICENOW_PLATFORM,
                source="servicenow-docs/update-sets",
                content="Update sets capture configuration changes.",
                version="washington",
            )
        ]
    )

    with pytest.raises(RetrievalBlocked) as exc:
        rags.retrieve_required_context("update set")

    assert "missing compliance context" in str(exc.value)


def test_cache_key_includes_source_hash_prompt_version_and_schema_version() -> None:
    first = cache_key(
        domain=RagDomain.COMPLIANCE,
        query="model policy",
        source_hash="abc123",
        prompt_version="prompt-v1",
        schema_version="schema-v1",
    )
    second = cache_key(
        domain=RagDomain.COMPLIANCE,
        query="model policy",
        source_hash="abc123",
        prompt_version="prompt-v2",
        schema_version="schema-v1",
    )

    assert first != second
    assert "abc123" in first
    assert "prompt-v1" in first
    assert "schema-v1" in first


def test_cross_domain_retrieval_does_not_leak_instance_metadata_into_compliance() -> None:
    rags = _rags()

    compliance_results = rags.retrieve(RagDomain.COMPLIANCE, "sp_instance")

    assert compliance_results == []


class RecordingPublicTransport:
    def __init__(self, response: PublicWebResponse | Exception) -> None:
        self.response = response
        self.urls: list[str] = []

    def get(self, url: str, *, timeout_seconds: float, max_bytes: int) -> PublicWebResponse:
        self.urls.append(url)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_public_web_retriever_fetches_allowlisted_https_docs_with_hash_citations() -> None:
    transport = RecordingPublicTransport(
        PublicWebResponse(
            url="https://docs.servicenow.com/bundle/yokohama-platform/page/administer.html",
            status_code=200,
            body=(
                b"<html><head><script>ignore()</script></head><body>"
                b"<h1>UI Policies</h1><p>UI policies make fields mandatory, visible, "
                b"or read-only without client scripts.</p></body></html>"
            ),
        )
    )
    retriever = PublicWebRetriever(
        config=PublicWebAccessConfig(
            allowed_domains=["docs.servicenow.com"],
            timeout_seconds=2.0,
            max_response_bytes=4096,
            max_excerpt_chars=80,
            max_results=2,
        ),
        transport=transport,
    )

    results = retriever.retrieve(
        "ServiceNow UI Policy docs",
        urls=["https://docs.servicenow.com/bundle/yokohama-platform/page/administer.html"],
    )

    assert transport.urls == [
        "https://docs.servicenow.com/bundle/yokohama-platform/page/administer.html"
    ]
    assert len(results) == 1
    assert results[0].content.startswith("UI Policies")
    assert "ignore()" not in results[0].content
    assert len(results[0].content) <= 80
    assert results[0].citation.source.startswith("public_web:")
    assert results[0].citation.content_hash
    assert results[0].citation.version == "live-public-web"


def test_public_web_retriever_blocks_disallowed_domain_before_transport() -> None:
    transport = RecordingPublicTransport(
        PublicWebResponse(url="https://evil.example/docs", status_code=200, body=b"bad")
    )
    retriever = PublicWebRetriever(
        config=PublicWebAccessConfig(allowed_domains=["docs.servicenow.com"]),
        transport=transport,
    )

    with pytest.raises(PublicWebRetrievalBlocked, match="not allowlisted"):
        retriever.retrieve("bad docs", urls=["https://evil.example/docs"])

    assert transport.urls == []


def test_public_web_retriever_blocks_private_hosts_and_non_https() -> None:
    retriever = PublicWebRetriever(
        config=PublicWebAccessConfig(allowed_domains=["docs.servicenow.com", "127.0.0.1"]),
        transport=RecordingPublicTransport(
            PublicWebResponse(url="https://docs.servicenow.com/docs", status_code=200, body=b"ok")
        ),
    )

    with pytest.raises(PublicWebRetrievalBlocked, match="https"):
        retriever.retrieve("bad docs", urls=["http://docs.servicenow.com/docs"])
    with pytest.raises(PublicWebRetrievalBlocked, match="private or loopback"):
        retriever.retrieve("bad docs", urls=["https://127.0.0.1/docs"])


def test_public_web_retriever_fails_closed_on_redirect_to_disallowed_domain() -> None:
    retriever = PublicWebRetriever(
        config=PublicWebAccessConfig(allowed_domains=["docs.servicenow.com"]),
        transport=RecordingPublicTransport(
            PublicWebResponse(
                url="https://evil.example/redirected",
                status_code=200,
                body=b"redirected body",
            )
        ),
    )

    with pytest.raises(PublicWebRetrievalBlocked, match="redirected"):
        retriever.retrieve(
            "redirect docs",
            urls=["https://docs.servicenow.com/bundle/yokohama-platform"],
        )
