# Sprint 538 Change Log

## ServiceNow dictionary column label write guard

Sprint 538 continued production hardening by tightening ServiceNow dictionary field creation. `ServiceNowClient.create_story_dictionary_field()` previously copied the requested dictionary `column_label` directly into the `sys_dictionary` JSON body, so malformed labels could reach OAuth token acquisition and request construction before failing downstream.

Dictionary field creation now validates `column_label` before constructing the request body. The guard allows normal human labels with spaces while rejecting non-string values, blank labels, trim-padded labels, control characters, and labels over 255 characters. Unsafe column labels fail with the fixed `ServiceNow dictionary column label is unsafe` diagnostic before OAuth token acquisition, POST construction, or Table API transport. The diagnostic does not echo column-label values, body fragments, or credential-like payloads.

This protects the `rm_story` bootstrap/write path that creates AI lifecycle fields while preserving the existing successful dictionary field creation behavior.

Verification:

- Added 1 failing-first ServiceNow dictionary column-label test proving unsafe dictionary labels are rejected before OAuth token acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_column_label_before_request -q`: failed before implementation because OAuth token acquisition was attempted before dictionary column-label validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_column_label_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_max_length_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_internal_type_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_element_before_request tests/test_servicenow.py::test_servicenow_client_creates_story_dictionary_field -q`: 5 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 117 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 612 tests passed after documentation updates.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues across 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2524 tests passed with 93.45% coverage.
