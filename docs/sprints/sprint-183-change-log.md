# Sprint 183 Change Log

Scope: Production hardening - alert webhook URL credential rejection.

## Changes

- Added fail-closed alert webhook URL validation for embedded URL credentials.
- `emit_alert_webhook()` now rejects URLs such as `https://user:password@example.gov/hook` before invoking transport.
- Kept the existing HTTPS-only requirement and pre-send oversized payload rejection.
- Documented the operator configuration posture in the external alert delivery section of the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_delivery.py -q` - 14 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 257 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 168 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1382 passed, 93.89% coverage.
