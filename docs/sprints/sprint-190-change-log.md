# Sprint 190 Change Log

Scope: Production hardening - sanitized ServiceNow request body byte redaction.

## Changes

- Updated `HttpRequest.sanitized()` to replace non-empty `body_bytes` with `b"***REDACTED***"` in diagnostic copies.
- Preserved original request `body_bytes` so binary attachments and webhook payload transport behavior remains unchanged.
- Added regression coverage proving sanitized request representations do not expose raw byte payload contents.
- Documented the sanitized byte-payload redaction behavior in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_http_request_sanitized_redacts_body_bytes_without_mutating_original tests/test_servicenow.py::test_redact_secrets_masks_sensitive_strings_under_non_sensitive_keys tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_with_binary_body -q` - 3 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 264 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1402 passed, 93.91% coverage.
