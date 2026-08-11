# Sprint 200 Change Log

Scope: Production hardening - camelCase sensitive-key redaction aliases.

## Changes

- Added regression coverage for camelCase sensitive assignment names such as `clientSecret=value` and `accessToken=value`.
- Added diagnostic URL query redaction coverage for camelCase sensitive query keys.
- Added alert webhook URL validation coverage for `clientSecret` query parameters.
- Added alert sink response and ServiceNow API diagnostic redaction coverage for structured `accessToken` and `clientSecret` keys.
- Extended the shared sensitive-key vocabulary with camelCase-compatible aliases for access, client, id, refresh, and vendor-style API credential keys.
- Documented camelCase sensitive-key aliases in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py tests/test_alert_webhook_url.py tests/test_alert_delivery.py::test_emit_alert_webhook_failure_redacts_sensitive_response_values tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values -q` - 31 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 274 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1432 passed, 93.92% coverage.
