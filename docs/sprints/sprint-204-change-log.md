# Sprint 204 Change Log

Scope: Production hardening - alert webhook local-target SSRF guard.

## Changes

- Added regression coverage for alert webhook URLs targeting `localhost`.
- Added regression coverage for IPv4 and IPv6 loopback targets.
- Added regression coverage for link-local metadata targets such as `169.254.169.254`.
- Added alert webhook host validation that rejects obvious local and link-local destinations without blocking all private-network alert sinks.
- Documented the local-target and link-local-target alert webhook safety rule in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py -q` - 17 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 278 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1451 passed, 93.92% coverage.
