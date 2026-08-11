# Sprint 208 Change Log

Scope: Production hardening - alert webhook URL encoded-control-character guard.

## Changes

- Added regression coverage for alert webhook URLs containing percent-encoded CR/LF characters such as `%0d%0a`.
- Added regression coverage for alert webhook URLs containing percent-encoded spaces such as `%20`.
- Extended shared alert webhook URL validation so startup validation and delivery-time validation reject percent-encoded whitespace and control characters before transport invocation.
- Documented the encoded whitespace/control-character rejection rule in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py -q` - 24 passed.
- `python3 -m pytest tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_url_encoded_control_characters tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_url_encoded_control_characters -q` - 2 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 282 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1466 passed, 93.93% coverage.
