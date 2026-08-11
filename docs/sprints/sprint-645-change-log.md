# Sprint 645 Change Log

## Discovery active metadata exact bool/string boundary

Sprint 645 continued production hardening by tightening `active` metadata consumed during ServiceNow surface discovery. The shared `_optional_bool()` helper still coerced arbitrary values with `str(value)`, so malformed in-process ServiceNow response objects could execute custom string conversion while business rule, client script, UI policy, flow, catalog, discovery-map, or integration surface records were being assembled.

Discovery active-state metadata now accepts only exact booleans or exact strings. ServiceNow-style strings such as `true`, `false`, `1`, `0`, `yes`, and `no` still parse normally. Objects, containers, numbers, booleans hidden behind subclasses, string subclasses, and unstringifiable values fail closed with `discovery active metadata is unsafe` before surface context is created.

Verification:

- Added 1 failing-first instance-discovery test proving a hostile active-state object executed `__str__` before implementation.
- `python3 -m pytest tests/test_instance_discovery.py::test_discover_surface_context_rejects_active_object_without_leak -q`: failed before implementation because the hostile `__str__` hook ran.
- `python3 -m pytest tests/test_instance_discovery.py::test_discover_surface_context_rejects_active_object_without_leak tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_related_platform_surfaces tests/test_instance_discovery.py::test_discover_dictionary_form_context_fetches_target_instance_state tests/test_instance_discovery.py::test_required_flow_graph_context_fails_closed_when_graph_is_incomplete tests/test_instance_discovery.py::test_resolve_fulfillment_flow_fails_closed_when_inactive tests/test_instance_discovery.py::test_resolve_fulfillment_flow_returns_active_record_triggered_flow -q`: 6 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_645_documents_discovery_active_metadata_boundary -q`: 1 test passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: no issues found in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 719 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2,780 tests passed with 93.03% coverage.
