# Sprint 536 Change Log

## ServiceNow dictionary internal type write guard

Sprint 536 continued production hardening by tightening ServiceNow dictionary field creation. `ServiceNowClient.create_story_dictionary_field()` previously copied the requested dictionary `internal_type` directly into the `sys_dictionary` JSON body, so malformed type values could reach OAuth token acquisition and request construction before failing downstream.

Dictionary field creation now validates `internal_type` before constructing the request body. The guard accepts only unpadded ServiceNow identifier-style type names, such as `string` or `glide_date_time`. Unsafe internal type values fail with the fixed `ServiceNow dictionary internal type is unsafe` diagnostic before OAuth token acquisition, POST construction, or Table API transport. The diagnostic does not echo internal type values, body fragments, or credential-like payloads.

This protects the `rm_story` bootstrap/write path that creates AI lifecycle fields while preserving the existing successful dictionary field creation behavior.

Verification:

- Added 1 failing-first ServiceNow dictionary internal type test proving unsafe dictionary type values are rejected before OAuth token acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_internal_type_before_request -q`: failed before implementation because OAuth token acquisition was attempted before dictionary internal type validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_internal_type_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_element_before_request tests/test_servicenow.py::test_servicenow_client_creates_story_dictionary_field -q`: 3 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 115 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 610 tests passed after documentation updates.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues across 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2520 tests passed with 93.45% coverage.
