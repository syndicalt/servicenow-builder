# Sprint 206 Change Log

Scope: Production hardening - unspecified alert webhook address guard.

## Changes

- Added regression coverage for alert webhook URLs targeting unspecified IPv4 addresses such as `0.0.0.0`.
- Added regression coverage for alert webhook URLs targeting unspecified IPv6 addresses such as `[::]`.
- Extended alert webhook host validation so unspecified IP addresses are rejected as unsafe local targets.
- Preserved the previous SSRF guard behavior for literal `localhost`, delegated `.localhost`, loopback, and link-local targets without blocking all private-network alert sinks.
- Documented unspecified address rejection in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py -q` - 20 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 280 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1456 passed, 93.92% coverage.
