# Sprint 188 Change Log

Scope: Production hardening - ServiceNow structured redaction vocabulary.

## Changes

- Refactored `servicenow.redact_secrets()` to use the shared `SENSITIVE_QUERY_KEYS` vocabulary.
- Extended ServiceNow structured redaction coverage for keys such as `api_key`, `token`, `signature`, and `id_token`.
- Preserved existing masking for `authorization`, `client_secret`, `access_token`, `refresh_token`, and `password`.
- Documented that ServiceNow API diagnostic redaction now uses the same sensitive-key vocabulary as runtime diagnostics and alert handling.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values_inside_lists tests/test_servicenow.py::test_servicenow_api_failure_raises_without_secret_leakage -q` - 5 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 262 passed.
- `python3 -m mypy src tests` - passed; 171 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1398 passed, 93.91% coverage.
