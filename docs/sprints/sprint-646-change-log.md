# Sprint 646 Change Log

## Discovery surface text metadata exact-string boundary

Sprint 646 continued production hardening by tightening shared text metadata consumed during ServiceNow surface discovery. Generic discovery surfaces still coerced record names, summaries, display/reference values, endpoint text before redaction, and selected reference metadata through `str()`, so malformed in-process ServiceNow response objects could execute conversion hooks while model context records were being assembled.

Shared ServiceNow surface discovery text metadata now accepts only exact strings or exact reference dictionaries whose `display_value` and `value` members are exact strings. String subclasses, object values, dict subclasses, nested containers, numbers, bytes, and unstringifiable values fail closed with `discovery text metadata contains non-JSON value` before surface context records, citations, or metadata summaries are created.

Verification:

- Added 1 failing-first instance-discovery test proving a hostile business-rule name object executed `__str__` before implementation.
- `python3 -m pytest tests/test_instance_discovery.py::test_discover_surface_context_rejects_name_object_without_leak -q`: failed before implementation because the hostile `__str__` hook ran.
- `python3 -m pytest tests/test_instance_discovery.py::test_discover_surface_context_rejects_name_object_without_leak tests/test_instance_discovery.py::test_discover_surface_context_rejects_active_object_without_leak tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_related_platform_surfaces tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_catalog_employee_center_surfaces tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_catalog_variable_sets_surface tests/test_instance_discovery.py::test_record_producer_story_requires_catalog_placement_surfaces tests/test_instance_discovery.py::test_required_form_section_context_collects_section_records -q`: 7 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_646_documents_discovery_text_metadata_boundary -q`: 1 test passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: no issues found in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 720 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2,782 tests passed with 93.01% coverage.
