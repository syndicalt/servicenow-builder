# Sprint 210 Change Log

Scope: Production hardening - alert webhook semicolon query separator sensitive-key guard.

## Changes

- Added regression coverage for alert webhook URLs that hide sensitive query keys behind semicolon separators such as `team=platform;token=secret`.
- Added regression coverage for semicolon-separated `client_secret` query parameters.
- Extended shared alert webhook URL validation so sensitive-query detection treats both `&` and `;` as query separators.
- Preserved existing ampersand-separated sensitive-query behavior, percent-encoded key handling, and delivery/runtime startup validation wiring.
- Documented semicolon-sensitive-query rejection in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py -q` - 35 passed.
- `python3 -m pytest tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_semicolon_sensitive_query_parameter tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_semicolon_sensitive_query_params -q` - 2 passed.
- `python3 -m pytest tests/test_alert_webhook_url.py --cov=jedi_devproject.alert_webhook_url --cov-report=term-missing -q` - 35 passed, 95.29% focused coverage.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 284 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1483 passed, 93.93% coverage.
