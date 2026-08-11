# Sprint 189 Change Log

Scope: Production hardening - shared diagnostic string redaction for ServiceNow API errors.

## Changes

- Added `jedi_devproject.diagnostic_redaction` as a neutral module for diagnostic string redaction.
- Kept `runtime_redaction._redact_diagnostic_text()` as a compatibility wrapper around the shared implementation.
- Extended `servicenow.redact_secrets()` to redact plain string values under non-sensitive keys, including ServiceNow `error.message` payloads.
- Covered URL passwords, sensitive query parameters, and assignment patterns such as `api_key=value` inside ServiceNow response diagnostics.
- Avoided the runtime config and ServiceNow circular import by moving diagnostic string redaction out of `runtime_redaction`.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_redact_secrets_masks_sensitive_strings_under_non_sensitive_keys tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values tests/test_runtime_redaction.py -q` - 5 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 263 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1400 passed, 93.91% coverage.
