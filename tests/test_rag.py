import pytest

from jedi_devproject.rag import (
    Document,
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
