# Sprint 184 Change Log

Scope: Production hardening - startup validation for alert webhook URL credentials.

## Changes

- Added runtime startup validation that rejects `JEDI_ALERT_WEBHOOK_URL` values containing embedded URL credentials when alert webhooks are enabled.
- Kept the existing startup checks for missing alert webhook URLs and non-HTTPS alert webhook URLs.
- Aligned startup validation with the delivery-time guard in `emit_alert_webhook()` so unsafe alert sink configuration fails before the API or worker starts.
- Documented the startup fail-closed behavior in the external alert delivery operator guidance.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_enabled_alert_webhook_without_url tests/test_runtime.py::test_validate_runtime_settings_rejects_non_https_alert_webhook_url tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_url_credentials -q` - 3 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 258 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 168 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1384 passed, 93.90% coverage.
