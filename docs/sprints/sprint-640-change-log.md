# Sprint 640 Change Log

## Public documentation content excerpt boundary

Sprint 640 continued production hardening by tightening public-documentation content excerpts inside ServiceNow surface context bundles. Prior hardening covered citation versions, sources, and content hashes. The retrieved `content` field still flowed into the `public_docs` surface record summary and excerpt-length metadata without an exact-string boundary.

The `public_docs` surface now accepts retrieved public-documentation content only when it is an exact string. Missing, non-string, string-subclass, or unstringifiable content values fail closed with `public documentation content contains non-JSON value` before model-facing record summaries or excerpt metadata are created.

Verification:

- Added 1 failing-first instance-discovery test proving a hostile public-doc content string subclass was accepted before implementation.
- `python3 -m pytest tests/test_instance_discovery.py::test_public_doc_surface_rejects_content_string_subclass_without_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_instance_discovery.py::test_public_doc_surface_rejects_content_string_subclass_without_leak tests/test_instance_discovery.py::test_public_doc_surface_rejects_content_hash_string_subclass_without_leak tests/test_instance_discovery.py::test_public_doc_surface_skips_version_string_subclass_without_leak tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_related_platform_surfaces tests/test_model_fulfillment.py::test_model_candidate_handler_adds_live_public_docs_to_packet -q`: 5 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 714 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2770 tests passed at 93.09% coverage.
