# Sprint 528 Change Log

## ServiceNow attachment metadata validation before file read

Sprint 528 continued production hardening by tightening ServiceNow attachment upload metadata. `ServiceNowClient.attach_story_file()` already validated the target story sys_id before reading local artifact bytes, but the attachment `file_name` query parameter and `content_type` request header were still accepted raw until after the artifact was read.

Attachment upload now validates both metadata values before local file IO, OAuth token acquisition, or Attachment API request construction. File names must be non-empty, unpadded, no longer than 255 characters, and free of path separators and control characters while still allowing ordinary internal spaces used by existing delivery artifact names. Content types must be simple MIME type/subtype tokens such as `application/xml`. Unsafe metadata fails with fixed diagnostics: `ServiceNow attachment file name is unsafe` or `ServiceNow attachment content type is unsafe`.

This keeps attachment handoff fail-closed for corrupted or hostile attachment metadata. Header-injection text, path material, URL fragments, and credential-like fragments are rejected without being echoed in diagnostics and before any local artifact read can occur.

Verification:

- Added 2 failing-first ServiceNow attachment metadata tests proving unsafe `file_name` and `content_type` values are rejected before `read_regular_artifact_bytes()` is called.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_file_name_before_read tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_content_type_before_read -q`: failed before implementation because the attachment file reader ran before metadata validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_file_name_before_read tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_content_type_before_read tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_with_binary_body tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_without_whole_file_read -q`: 4 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 107 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 602 documentation tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2504 tests passed with 93.43% coverage.
