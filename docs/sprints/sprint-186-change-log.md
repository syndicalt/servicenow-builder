# Sprint 186 Change Log

Scope: Production hardening - alert webhook URL sensitive-query rejection.

## Changes

- Added `jedi_devproject.sensitive_keys.SENSITIVE_QUERY_KEYS` as the neutral source for common credential-bearing key names.
- Refactored runtime diagnostic redaction and alert response redaction to use the neutral sensitive-key module.
- Extended `validate_alert_webhook_url()` to reject alert sink URLs containing sensitive query parameters such as `token`, `access_token`, `signature`, and `client_secret`.
- Covered both delivery-time validation and production startup validation for sensitive-query alert webhook URLs.
- Documented the fail-closed alert URL posture in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_sensitive_query_params tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_non_https_url tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_url_embedded_credentials -q` - 9 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 260 passed.
- `python3 -m mypy src tests` - passed; 171 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1393 passed, 93.90% coverage.
