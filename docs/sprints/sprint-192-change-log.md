# Sprint 192 Change Log

Scope: Production hardening - authorization scheme diagnostic redaction.

## Changes

- Extended shared diagnostic string redaction for `Authorization: Bearer <token>` and `Authorization: Basic <token>` diagnostics.
- Preserved the authorization scheme in diagnostics while masking the credential value.
- Kept generic sensitive assignment redaction for values such as `client_secret=value` and `access_token: value`.
- Covered the shared runtime redaction path, which also protects ServiceNow response diagnostic strings.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py tests/test_servicenow.py::test_redact_secrets_masks_sensitive_strings_under_non_sensitive_keys -q` - 3 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 266 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1406 passed, 93.92% coverage.
