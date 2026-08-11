# Sprint 199 Change Log

Scope: Production hardening - vendor-style `x-*` sensitive-key redaction.

## Changes

- Added regression coverage for `x-api-key` and `x-client-secret` across diagnostic assignments and diagnostic URL query parameters.
- Added alert webhook URL validation coverage for `x-api-key` query parameters.
- Added alert sink response and ServiceNow API diagnostic redaction coverage for structured `x-api-key` and `x-client-secret` keys.
- Extended the shared sensitive-key vocabulary with `x_api_key` and `x_client_secret`, which also covers hyphenated spellings through shared key normalization.
- Documented vendor-style `x-*` sensitive-key redaction in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_redaction.py tests/test_alert_webhook_url.py tests/test_alert_delivery.py::test_emit_alert_webhook_failure_redacts_sensitive_response_values tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values -q` - 27 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 273 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1427 passed, 93.92% coverage.
