# Sprint 263 Change Log - ServiceNow Attachment Upload Size Guard

## Summary

- ServiceNow story attachment uploads now have a 10 MiB file-size cap before reading file contents into memory.
- Added a failing regression proving oversized attachment files raise `ServiceNowApiError` before any OAuth token request or Attachment API upload is sent.
- Added a named `MAX_ATTACHMENT_UPLOAD_BYTES` constant so tests, code, and operator documentation share the same upload boundary.
- Preserved the existing binary attachment upload behavior for files within the cap.
- Documented the attachment upload size guard in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_with_binary_body tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_attachment_before_reading tests/test_servicenow.py::test_http_request_sanitized_redacts_body_bytes_without_mutating_original -q` - 3 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/servicenow.py tests/test_servicenow.py` - success: no issues found in 2 source files.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_with_binary_body tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_attachment_before_reading tests/test_servicenow.py::test_http_request_sanitized_redacts_body_bytes_without_mutating_original tests/test_project_docs.py::test_sprint_two_hundred_sixty_three_documents_attachment_upload_size_guard -q` - 4 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - all checks passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 337 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1658 passed, total coverage 93.96%.
