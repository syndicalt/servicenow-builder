# Sprint 197 Change Log

Scope: Production hardening - hyphenated sensitive-key redaction.

## Changes

- Added a shared sensitive-key normalization helper so structured redaction treats hyphenated and underscored credential names consistently.
- Extended diagnostic assignment redaction for hyphenated names such as `api-key=value` and `client-secret=value`.
- Extended diagnostic URL query redaction for hyphenated sensitive query keys such as `api-key=secret`.
- Updated ServiceNow request/response redaction and alert response redaction to mask structured keys such as `api-key` and `client-secret`.
- Updated alert webhook URL validation to reject sensitive query parameters using hyphenated key names.
- Documented hyphenated sensitive-key redaction in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py tests/test_alert_webhook_url.py tests/test_alert_delivery.py::test_emit_alert_webhook_failure_redacts_sensitive_response_values tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values -q` - 22 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 271 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1420 passed, 93.92% coverage.
