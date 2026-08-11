# Sprint 529 Change Log

## ServiceNow attachment read-error path redaction

Sprint 529 continued production hardening by removing local filesystem path material from ServiceNow attachment upload read-error diagnostics. `ServiceNowClient.attach_story_file()` already rejected symlinked and non-regular artifact paths before upload, but the regular-file failure branch appended the submitted `file_path` to the `ServiceNowApiError` message. A copied path could include workspace structure, URL fragments, tenant identifiers, or credential-like filename material.

Symlinked and non-regular attachment paths now fail with the fixed diagnostic `ServiceNow attachment file must be a regular file`. The diagnostic does not echo local path values, filenames, URL fragments, or credential-like payloads. The oversized-file branch remains typed through `ArtifactReadError.reason` and continues to report the configured upload byte limit.

This keeps attachment handoff fail-closed without turning local filesystem paths into ServiceNow work-note, CLI, worker-log, or admin-console diagnostics.

Verification:

- Added 1 failing-first ServiceNow attachment read-error test proving a secret-bearing symlink path is rejected without echoing the path or filename fragments.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_symlinked_story_attachment_before_upload -q`: failed before implementation because the diagnostic appended the absolute attachment path and `client_secret` filename fragment.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_symlinked_story_attachment_before_upload tests/test_servicenow.py::test_servicenow_client_attachment_read_error_uses_typed_reason_not_message_prefix -q`: 2 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 107 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 603 documentation tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2505 tests passed with 93.43% coverage.
