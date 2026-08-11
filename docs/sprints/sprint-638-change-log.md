# Sprint 638 Change Log

## Public documentation context-bundle citation version boundary

Sprint 638 continued production hardening by tightening public-documentation citation metadata inside ServiceNow surface context bundles. Sprint 634 already protected the path that folds public documentation into RAG documents. The remaining bundle path still used `str(result.citation.version or "")` while building the `public_docs` surface, so a corrupted in-process retriever result could execute custom string conversion while `instance_context_bundle` record metadata or citation dictionaries were being created.

The `public_docs` surface now copies citation versions only when they are exact strings. Missing, non-string, string-subclass, or unstringifiable citation versions become an empty string before context-bundle records or citations are persisted.

Verification:

- Added 1 failing-first instance-discovery test proving a hostile citation version string subclass was accepted before implementation.
- `python3 -m pytest tests/test_instance_discovery.py::test_public_doc_surface_skips_version_string_subclass_without_leak -q`: failed before implementation because the hostile `client_secret` string was written into bundle metadata.
- `python3 -m pytest tests/test_instance_discovery.py::test_public_doc_surface_skips_version_string_subclass_without_leak tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_related_platform_surfaces tests/test_model_fulfillment.py::test_model_candidate_handler_adds_live_public_docs_to_packet tests/test_model_fulfillment.py::test_model_candidate_handler_skips_provider_when_required_public_docs_missing -q`: 4 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 712 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2766 tests passed at 93.09% coverage.
