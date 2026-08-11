# Sprint 193 Change Log

Scope: Production hardening - malformed diagnostic URL fail-closed redaction.

## Changes

- Added regression coverage for quote-wrapped sensitive assignments such as `client_secret="value"` and `token='value'`.
- Added fail-closed diagnostic URL redaction when a malformed URL with secret userinfo cannot be safely reconstructed.
- Fixed bad-port URL handling so redaction returns `***REDACTED***` instead of raising during diagnostic formatting.
- Covered the shared runtime redaction path, which also protects ServiceNow response diagnostic strings.
- Documented malformed diagnostic URL redaction in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py tests/test_servicenow.py::test_redact_secrets_masks_sensitive_strings_under_non_sensitive_keys -q` - 5 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 267 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1409 passed, 93.92% coverage.
