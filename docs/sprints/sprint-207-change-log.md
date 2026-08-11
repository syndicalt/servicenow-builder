# Sprint 207 Change Log

Scope: Production hardening - alert webhook URL whitespace/control-character guard.

## Changes

- Added regression coverage for alert webhook URLs containing raw newline/control characters.
- Added regression coverage for alert webhook URLs containing raw whitespace in the URL.
- Extended shared alert webhook URL validation so startup validation and delivery-time validation reject raw whitespace and ASCII control characters before parsing or transport invocation.
- Documented the whitespace/control-character rejection rule in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py -q` - 22 passed.
- `python3 -m pytest tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_url_control_characters tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_url_control_characters -q` - 2 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 281 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1461 passed, 93.92% coverage.
