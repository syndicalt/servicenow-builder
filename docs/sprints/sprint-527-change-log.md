# Sprint 527 Change Log

## ServiceNow attachment story-id validation before file read

Sprint 527 continued production hardening by tightening the ordering of ServiceNow attachment upload validation. `ServiceNowClient.attach_story_file()` previously read the local attachment artifact before validating the target story sys_id used as the Attachment API `table_sys_id` parameter. A malformed story id could therefore trigger local file IO before the request was rejected or failed later.

Attachment upload now validates `story_sys_id` with the ServiceNow record-id path safety rule before reading the attachment file, acquiring an OAuth token, or constructing the Attachment API request. Unsafe story ids fail with the fixed `ServiceNow API record id is unsafe` diagnostic. The diagnostic does not echo record id values, URL fragments, credential-like fragments, or request parameter values.

This keeps attachment handoff fail-closed and cheap for corrupted or hostile target ids: unsupported path material fails before local artifact reads and before any ServiceNow request can be constructed.

Verification:

- Added 1 failing-first ServiceNow attachment story-id test proving unsafe target ids are rejected before `read_regular_artifact_bytes()` is called.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_story_id_before_read -q`: failed before implementation because the attachment file reader ran before story id validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_story_id_before_read -q`: 1 test passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 105 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 601 documentation tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2501 tests passed with 93.43% coverage.
