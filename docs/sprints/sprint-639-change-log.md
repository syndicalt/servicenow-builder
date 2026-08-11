# Sprint 639 Change Log

## Public documentation required citation metadata boundary

Sprint 639 continued production hardening by tightening required public-documentation citation metadata inside ServiceNow surface context bundles. Sprint 638 made optional citation versions exact-string only. The required `source` and `content_hash` fields still flowed into `public_docs` records, citation dictionaries, and `public_web:<hash>` evidence entries without an exact-string boundary.

The `public_docs` surface now accepts citation `source` and `content_hash` only when they are exact strings. Missing, non-string, string-subclass, or unstringifiable values fail closed with `public documentation citation contains non-JSON value` before context-bundle records, citations, or evidence strings are created.

Verification:

- Added 1 failing-first instance-discovery test proving a hostile `content_hash` string subclass was accepted before implementation.
- `python3 -m pytest tests/test_instance_discovery.py::test_public_doc_surface_rejects_content_hash_string_subclass_without_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_instance_discovery.py::test_public_doc_surface_rejects_content_hash_string_subclass_without_leak tests/test_instance_discovery.py::test_public_doc_surface_skips_version_string_subclass_without_leak tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_related_platform_surfaces tests/test_model_fulfillment.py::test_model_candidate_handler_adds_live_public_docs_to_packet -q`: 4 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 713 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2768 tests passed at 93.09% coverage.
