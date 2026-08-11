# Sprint 642 Change Log

## Public documentation citation confidence formatting boundary

Sprint 642 continued production hardening by tightening public-documentation citation confidence inside ServiceNow surface context bundles. Prior hardening covered public-doc citation strings, retrieved content, and query evidence. Confidence still flowed into `public_docs` record metadata and citation dictionaries through Python format strings, which meant a corrupted in-process retriever result could execute custom `__format__` behavior while model-facing context was being assembled.

The `public_docs` surface now accepts citation confidence only when it is an exact integer or float in the inclusive `0..1` range. Objects, strings, booleans, subclasses, non-finite numbers, and out-of-range values fail closed with `public documentation citation confidence is unsafe` before record metadata or citation dictionaries are created.

Verification:

- Added 1 failing-first instance-discovery test proving a hostile confidence object was accepted before implementation.
- `python3 -m pytest tests/test_instance_discovery.py::test_public_doc_surface_rejects_confidence_object_without_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_instance_discovery.py::test_public_doc_surface_rejects_confidence_object_without_leak tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_related_platform_surfaces tests/test_model_fulfillment.py::test_model_candidate_handler_adds_live_public_docs_to_packet tests/test_instance_discovery.py::test_public_doc_surface_rejects_query_string_subclass_without_leak -q`: 4 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 716 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2774 tests passed at 93.09% coverage.
