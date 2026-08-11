# Sprint 185 Change Log

Scope: Production hardening - shared alert webhook URL validator.

## Changes

- Added `jedi_devproject.alert_webhook_url.validate_alert_webhook_url()` as the single validator for external alert sink URLs.
- Refactored `emit_alert_webhook()` to use the shared validator before transport invocation.
- Refactored runtime startup validation to use the same helper with `JEDI_ALERT_WEBHOOK_URL` subject text.
- Preserved existing behavior for HTTPS enforcement and embedded credential rejection while removing validation drift between startup and delivery-time checks.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py tests/test_alert_delivery.py tests/test_runtime.py::test_validate_runtime_settings_rejects_enabled_alert_webhook_without_url tests/test_runtime.py::test_validate_runtime_settings_rejects_non_https_alert_webhook_url tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_url_credentials -q` - 21 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 259 passed.
- `python3 -m mypy src tests` - passed; 170 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1389 passed, 93.90% coverage.
