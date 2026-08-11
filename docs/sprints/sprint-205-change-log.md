# Sprint 205 Change Log

Scope: Production hardening - delegated `.localhost` alert webhook target guard.

## Changes

- Added regression coverage for alert webhook URLs targeting delegated `.localhost` names such as `alerts.localhost`.
- Extended alert webhook host validation so any hostname ending in `.localhost` is rejected as a local target.
- Preserved the previous scope of the SSRF guard: literal `localhost`, IPv4 and IPv6 loopback, and link-local targets remain rejected without blocking all private-network alert sinks.
- Documented delegated `.localhost` alert webhook target rejection in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py -q` - 18 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 279 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1453 passed, 93.92% coverage.
