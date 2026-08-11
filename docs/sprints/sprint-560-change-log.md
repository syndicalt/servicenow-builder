# Sprint 560 Change Log

## ServiceNow attachment content-type length guard

Sprint 560 continued production hardening by bounding ServiceNow attachment upload content types. `_servicenow_attachment_content_type()` already rejected non-string values, padded values, header-injection whitespace, controls, parameters, and malformed MIME tokens before `ServiceNowClient.attach_story_file()` read local artifact bytes, but it did not cap otherwise valid MIME token strings.

Attachment content-type validation now rejects values longer than 255 characters before local artifact reads, OAuth token acquisition, Attachment API request construction, or upload transport. Oversized content types fail with the fixed `ServiceNow attachment content type is unsafe` diagnostic. The diagnostic does not echo submitted metadata values, object representations, URL fragments, header-injection text, or credential-like payloads.

This keeps delivery attachment handoff fail-closed when a caller supplies syntactically valid but unbounded Content-Type header material.

Verification:

- Added 1 failing-first ServiceNow attachment content-type length test proving a regex-valid oversized content type reached `read_regular_artifact_bytes()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_attachment_content_type_before_read -q`: failed before implementation because the oversized content type reached local artifact read.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_attachment_content_type_before_read tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_content_type_before_read tests/test_servicenow.py::test_servicenow_client_rejects_non_string_attachment_content_type_before_read tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_file_name_before_read tests/test_servicenow.py::test_servicenow_client_rejects_non_string_attachment_file_name_before_read tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_with_binary_body -q`: 6 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 162 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 634 passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2591 passed, 93.41% total coverage.
