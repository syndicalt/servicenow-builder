# Sprint 3 Change Log

## Scope

Sprint 3 created specialized RAG boundaries and local deterministic retrieval before any external vector store or model integration.

## Changes

- Specialized RAG boundaries in `src/jedi_devproject/rag.py`.
- `RagDomain` for ServiceNow platform, instance metadata, project context, and compliance retrieval.
- `Document` and `RetrievalResult` models for local retrieval inputs and outputs.
- Local deterministic retrieval through `LocalRagIndex`.
- `SpecializedRags` facade that keeps each domain in its own index.
- Retrieval citations built with source, version, confidence, and stable content hash.
- Compliance context blocking through `retrieve_required_context`.
- Cross-domain isolation verified so compliance retrieval does not leak instance metadata.
- Cache key helper that includes domain, query, source hash, prompt version, and schema version.

## Assumptions Challenged

- A single broad vector index would be simpler, but it would weaken auditability and increase cross-domain leakage risk.
- Local deterministic retrieval is sufficient for Sprint 3 because the goal is interface and orchestration safety, not semantic search quality.
- Compliance context is mandatory for candidate generation; missing compliance context blocks the workflow instead of allowing ungrounded generation.

## Verification Evidence

Latest full gate run before this change log was added:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result:

- Ruff passed.
- Mypy passed.
- Pytest passed with 35 tests.
- Coverage was 97.27%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
