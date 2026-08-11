# Sprint 641 Change Log

## Public documentation query evidence boundary

Sprint 641 continued production hardening by tightening public-documentation query strings inside ServiceNow surface context bundles. Prior hardening covered public-doc citation metadata and retrieved content excerpts. Query entries still flowed into `instance_context_bundle.public_doc_queries` and `public_docs:<query>` evidence strings without an exact-string boundary.

The context bundle now accepts public-documentation query entries only when they are exact strings. Missing, non-string, string-subclass, or unstringifiable query values fail closed with `public documentation query contains non-JSON value` before bundle persistence or model context assembly.

Verification:

- Added 1 failing-first instance-discovery test proving a hostile public-doc query string subclass was accepted before implementation.
- `python3 -m pytest tests/test_instance_discovery.py::test_public_doc_surface_rejects_query_string_subclass_without_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_instance_discovery.py::test_public_doc_surface_rejects_query_string_subclass_without_leak tests/test_instance_discovery.py::test_required_public_docs_without_results_are_insufficient tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_related_platform_surfaces tests/test_model_fulfillment.py::test_model_candidate_handler_adds_live_public_docs_to_packet -q`: 4 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 715 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2772 tests passed at 93.10% coverage.
