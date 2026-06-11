import pytest

from jedi_devproject.models import RetrievalCitation
from jedi_devproject.rag import (
    Document,
    LocalRagIndex,
    PublicWebAccessConfig,
    PublicWebResponse,
    PublicWebRetrievalBlocked,
    PublicWebRetriever,
    RagDomain,
    RetrievalBlocked,
    RetrievalResult,
    SpecializedRags,
    cache_key,
)
from jedi_devproject.rag_cache import RetrievalCache, RetrievalCacheStats


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


class CountingIndex(LocalRagIndex):
    def __init__(self, *, domain: RagDomain, documents: list[Document]) -> None:
        super().__init__(domain=domain, documents=documents)
        self.retrieve_calls = 0

    def retrieve(self, query: str) -> list[RetrievalResult]:
        self.retrieve_calls += 1
        return super().retrieve(query)


def _base_documents(*, compliance_version: str = "2026-05") -> list[Document]:
    return [
        Document(
            domain=RagDomain.SERVICENOW_PLATFORM,
            source="servicenow-docs/update-sets",
            content="Update sets capture portal configuration changes for review.",
            version="washington",
        ),
        Document(
            domain=RagDomain.COMPLIANCE,
            source="policy/model-use",
            content="Portal work must not use public AI endpoints unless explicitly approved.",
            version=compliance_version,
        ),
        Document(
            domain=RagDomain.PUBLIC_DOCUMENTATION,
            source="public_web:https://docs.servicenow.com/ui-policy",
            content="UI policies control portal field behavior.",
            version="live-public-web",
        ),
    ]


def _counting_rags(
    documents: list[Document],
    *,
    cache: RetrievalCache[RetrievalResult] | None = None,
    cache_enabled: bool = True,
) -> tuple[SpecializedRags, dict[RagDomain, CountingIndex]]:
    indexes = {domain: CountingIndex(domain=domain, documents=documents) for domain in RagDomain}
    rags = SpecializedRags(indexes=dict(indexes), cache=cache, cache_enabled=cache_enabled)
    return rags, indexes


def test_repeated_retrieval_is_served_from_cache() -> None:
    rags, indexes = _counting_rags(_base_documents())

    first = rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "portal")
    second = rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "portal")

    assert first
    assert indexes[RagDomain.SERVICENOW_PLATFORM].retrieve_calls == 1
    assert [result.model_dump() for result in first] == [
        result.model_dump() for result in second
    ]
    stats = rags.cache_stats
    assert stats is not None
    assert stats.hits == 1
    assert stats.misses == 1
    assert stats.size == 1


def test_cache_hit_preserves_citation_confidence_and_version() -> None:
    rags, _ = _counting_rags(_base_documents())

    rags.retrieve(RagDomain.COMPLIANCE, "portal")
    cached = rags.retrieve(RagDomain.COMPLIANCE, "portal")

    assert cached[0].citation.source == "policy/model-use"
    assert cached[0].citation.content_hash
    assert cached[0].citation.confidence == 1.0
    assert cached[0].citation.version == "2026-05"


def test_different_queries_do_not_share_cache_entries() -> None:
    rags, indexes = _counting_rags(_base_documents())

    rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "portal")
    rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "update sets")

    assert indexes[RagDomain.SERVICENOW_PLATFORM].retrieve_calls == 2


def test_corpus_version_change_invalidates_cache_key() -> None:
    shared: RetrievalCache[RetrievalResult] = RetrievalCache()
    rags_v1, _ = _counting_rags(_base_documents(compliance_version="2026-05"), cache=shared)
    rags_v2, indexes_v2 = _counting_rags(
        _base_documents(compliance_version="2026-06"), cache=shared
    )

    rags_v1.retrieve(RagDomain.COMPLIANCE, "portal")
    results_v2 = rags_v2.retrieve(RagDomain.COMPLIANCE, "portal")

    assert indexes_v2[RagDomain.COMPLIANCE].retrieve_calls == 1
    assert results_v2[0].citation.version == "2026-06"
    assert shared.stats.hits == 0
    assert shared.stats.misses == 2


def test_mutating_returned_results_does_not_poison_cache() -> None:
    rags, _ = _counting_rags(_base_documents())

    first = rags.retrieve(RagDomain.COMPLIANCE, "portal")
    first[0].content = "tampered"
    first[0].citation.confidence = 0.1

    second = rags.retrieve(RagDomain.COMPLIANCE, "portal")
    assert second[0].content.startswith("Portal work")
    assert second[0].citation.confidence == 1.0


def test_cache_eviction_is_bounded_and_lru_ordered() -> None:
    cache: RetrievalCache[RetrievalResult] = RetrievalCache(max_entries=2)
    rags, indexes = _counting_rags(_base_documents(), cache=cache)
    platform = indexes[RagDomain.SERVICENOW_PLATFORM]

    rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "portal")  # miss
    rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "update")  # miss
    rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "portal")  # hit, refresh recency
    rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "changes")  # miss, evicts "update"
    rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "portal")  # hit, kept by LRU refresh
    rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "update")  # miss, was evicted

    assert platform.retrieve_calls == 4
    assert cache.stats.hits == 2
    assert cache.stats.misses == 4
    assert cache.stats.size == 2


def test_disabled_cache_passes_every_retrieval_through_to_indexes() -> None:
    rags, indexes = _counting_rags(_base_documents(), cache_enabled=False)

    rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "portal")
    rags.retrieve(RagDomain.SERVICENOW_PLATFORM, "portal")

    assert indexes[RagDomain.SERVICENOW_PLATFORM].retrieve_calls == 2
    assert rags.cache_stats is None


def test_public_documentation_domain_is_never_cached() -> None:
    rags, indexes = _counting_rags(_base_documents())

    rags.retrieve(RagDomain.PUBLIC_DOCUMENTATION, "portal")
    rags.retrieve(RagDomain.PUBLIC_DOCUMENTATION, "portal")

    assert indexes[RagDomain.PUBLIC_DOCUMENTATION].retrieve_calls == 2
    stats = rags.cache_stats
    assert stats is not None
    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.size == 0


def test_retrieve_required_context_reuses_cached_domain_results() -> None:
    rags, indexes = _counting_rags(_base_documents())

    first = rags.retrieve_required_context("portal")
    second = rags.retrieve_required_context("portal")

    assert first == second
    for domain in RagDomain:
        expected = 2 if domain is RagDomain.PUBLIC_DOCUMENTATION else 1
        assert indexes[domain].retrieve_calls == expected


def test_from_documents_cache_flag_propagates_through_with_documents() -> None:
    enabled = SpecializedRags.from_documents(_base_documents())
    disabled = SpecializedRags.from_documents(_base_documents(), cache_enabled=False)

    assert enabled.cache_stats is not None
    assert enabled.with_documents([]).cache_stats is not None
    assert disabled.cache_stats is None
    assert disabled.with_documents([]).cache_stats is None


def test_retrieval_cache_rejects_non_positive_max_entries() -> None:
    with pytest.raises(ValueError, match="max_entries"):
        RetrievalCache(max_entries=0)


def test_retrieval_cache_put_stores_defensive_copies_and_clear_resets() -> None:
    cache: RetrievalCache[RetrievalResult] = RetrievalCache(max_entries=4)
    result = RetrievalResult(
        content="original",
        citation=RetrievalCitation(
            source="policy/model-use",
            content_hash="hash-1",
            confidence=0.9,
            version="v1",
        ),
    )

    cache.put("key", [result])
    result.content = "tampered after put"

    cached = cache.get("key")
    assert cached is not None
    assert cached[0].content == "original"

    cache.clear()
    assert cache.get("key") is None
    assert cache.stats.size == 0


def test_retrieval_cache_stats_hit_rate() -> None:
    assert RetrievalCacheStats(hits=0, misses=0, size=0, max_size=8).hit_rate == 0.0
    assert RetrievalCacheStats(hits=3, misses=1, size=2, max_size=8).hit_rate == 0.75
