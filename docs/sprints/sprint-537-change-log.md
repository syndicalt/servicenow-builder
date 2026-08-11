# Sprint 537 Change Log

## ServiceNow dictionary max length write guard

Sprint 537 continued production hardening by tightening ServiceNow dictionary field creation. `ServiceNowClient.create_story_dictionary_field()` previously converted the requested dictionary `max_length` with `str(max_length)` when present, so malformed values could reach OAuth token acquisition and request construction before failing downstream.

Dictionary field creation now validates `max_length` before constructing the request body. The guard accepts only real Python integers from 1 through 65535 and rejects booleans, strings, non-integers, non-positive values, and oversized values. Unsafe max-length values fail with the fixed `ServiceNow dictionary max length is unsafe` diagnostic before OAuth token acquisition, POST construction, or Table API transport. The diagnostic does not echo max-length values, body fragments, or credential-like payloads.

This protects the `rm_story` bootstrap/write path that creates AI lifecycle fields while preserving the existing successful dictionary field creation behavior.

Verification:

- Added 1 failing-first ServiceNow dictionary max-length test proving unsafe dictionary max-length values are rejected before OAuth token acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_max_length_before_request -q`: failed before implementation because OAuth token acquisition was attempted before dictionary max-length validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_max_length_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_internal_type_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_element_before_request tests/test_servicenow.py::test_servicenow_client_creates_story_dictionary_field -q`: 4 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 116 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 611 tests passed after documentation updates.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues across 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2522 tests passed with 93.45% coverage.
