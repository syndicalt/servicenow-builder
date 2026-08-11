# Sprint 539 Change Log

## ServiceNow story PATCH field-name guard

Sprint 539 continued production hardening by tightening ServiceNow story updates. `ServiceNowClient.update_story_fields()` previously validated the story `sys_id` path segment but copied PATCH body field names directly into the `rm_story` JSON body, so malformed field names could reach OAuth token acquisition and request construction before failing downstream.

Story field updates now validate every PATCH body field name with the shared ServiceNow field identifier guard before constructing the request. Unsafe field names fail with the fixed `ServiceNow API field name is unsafe` diagnostic before OAuth token acquisition, PATCH construction, or Table API transport. The diagnostic does not echo field names, body fragments, or credential-like payloads.

This protects story state, AI status, handoff reference, artifact reference, and work-note writeback paths while preserving existing successful story PATCH behavior and values.

Verification:

- Added 1 failing-first ServiceNow story PATCH field-name test proving unsafe PATCH body field names are rejected before OAuth token acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_patch_field_before_request -q`: failed before implementation because OAuth token acquisition was attempted before PATCH body field-name validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_patch_field_before_request tests/test_servicenow.py::test_servicenow_client_updates_story_fields_with_patch_without_secret_leakage tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_record_id_before_request -q`: 3 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 118 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 613 tests passed after documentation updates.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues across 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2526 tests passed with 93.45% coverage.
