# Sprint 634 Change Log

## Public documentation citation version exact-string boundary

Sprint 634 continued production hardening by tightening the model-fulfillment path that folds live public-documentation retrieval results into the specialized RAG corpus. The previous path called `str(result.citation.version or "")`, so corrupted in-process retriever results could execute custom conversion or leak fragments while public-doc evidence was being added to the model context.

Public-documentation citation versions now pass through `_public_doc_citation_version()`. The helper accepts only exact string versions and falls back to an empty string for missing, non-string, string-subclass, or unstringifiable values. Valid retrieved public documentation still enters the RAG corpus unchanged.

Verification:

- Added 1 failing-first model fulfillment test proving hostile public-doc citation version metadata executed before implementation.
- `python3 -m pytest tests/test_model_fulfillment.py::test_surface_context_public_doc_version_skips_malformed_metadata_without_coercion -q`: failed before implementation with the hostile `public-doc-version-secret` exception.
- `python3 -m pytest tests/test_model_fulfillment.py::test_surface_context_public_doc_version_skips_malformed_metadata_without_coercion tests/test_model_fulfillment.py::test_model_candidate_handler_adds_live_public_docs_to_packet tests/test_model_fulfillment.py::test_model_candidate_handler_skips_provider_when_required_public_docs_missing -q`: 3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 708 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2757 tests passed at 93.08% coverage.
