# Sprint 535 Change Log

## ServiceNow dictionary element write guard

Sprint 535 continued production hardening by tightening ServiceNow dictionary field creation. `ServiceNowClient.create_story_dictionary_field()` previously copied the requested dictionary `element` directly into the `sys_dictionary` JSON body, so malformed element names could reach OAuth token acquisition and request construction before failing downstream.

Dictionary field creation now validates `element` with the shared ServiceNow field identifier guard before constructing the request body. Unsafe element names fail with the fixed `ServiceNow API field name is unsafe` diagnostic before OAuth token acquisition, POST construction, or Table API transport. The diagnostic does not echo element values, encoded-query fragments, or credential-like payloads.

This protects the `rm_story` bootstrap/write path that creates AI lifecycle fields while preserving the existing successful dictionary field creation behavior.

Verification:

- Added 1 failing-first ServiceNow dictionary element test proving unsafe dictionary element names are rejected before OAuth token acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_element_before_request -q`: failed before implementation because OAuth token acquisition was attempted before dictionary element validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_element_before_request tests/test_servicenow.py::test_servicenow_client_creates_story_dictionary_field -q`: 2 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 114 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 609 tests passed after documentation updates.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues across 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2518 tests passed with 93.44% coverage.
