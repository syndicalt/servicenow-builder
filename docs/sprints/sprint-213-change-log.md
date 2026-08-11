# Sprint 213 Change Log

Scope: Production hardening - alert webhook Unicode-dot local-target guard.

## Changes

- Added regression coverage for alert webhook URLs targeting `localhost。`.
- Added regression coverage for alert webhook URLs targeting Unicode-dot loopback forms such as `127。0。0。1`.
- Extended shared alert webhook host normalization so Unicode DNS dot aliases are canonicalized to `.` before local, link-local, unspecified, and legacy numeric target checks.
- Preserved existing normal `localhost`, `.localhost`, loopback, link-local, unspecified, and legacy numeric target rejection behavior.
- Documented Unicode-dot local-target rejection in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py -q` - 43 passed.
- `python3 -m pytest tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_unicode_dot_loopback_url tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_unicode_dot_loopback -q` - 2 passed.
- `python3 -m pytest tests/test_alert_webhook_url.py --cov=jedi_devproject.alert_webhook_url --cov-report=term-missing -q` - 43 passed, 95.41% focused coverage.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 287 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1500 passed, 93.93% coverage.
