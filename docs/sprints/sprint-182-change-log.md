# Sprint 182 Change Log

Scope: Production hardening - shared sensitive-key alert response redaction.

## Changes

- Updated external alert webhook response redaction to use the shared runtime sensitive-key vocabulary for structured JSON keys.
- Covered structured alert sink response keys such as `api_key`, `token`, `signature`, `secret`, `id_token`, `code`, `client_secret`, and `access_token`.
- Kept existing recursive diagnostic-string redaction for `client_secret=value`, URL passwords, and sensitive query parameters.
- Documented the operator behavior in the external alert delivery section of the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_delivery.py -q` - 13 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 256 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 168 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1380 passed, 93.88% coverage.
