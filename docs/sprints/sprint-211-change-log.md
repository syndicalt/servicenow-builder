# Sprint 211 Change Log

Scope: Production hardening - alert webhook encoded query separator sensitive-key guard.

## Changes

- Added regression coverage for alert webhook URLs that hide sensitive query keys behind encoded ampersand separators such as `team=platform%26token=secret`.
- Added regression coverage for encoded semicolon separators such as `team=platform%3Bclient_secret=secret`.
- Added positive coverage showing benign encoded separator values such as `note=fish%26chips` remain allowed.
- Extended shared alert webhook URL validation so sensitive-query detection evaluates both the raw query string and a percent-decoded query string before startup validation or delivery-time transport invocation.
- Documented encoded query separator sensitive-key rejection in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py -q` - 38 passed.
- `python3 -m pytest tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_encoded_separator_sensitive_query_parameter tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_encoded_separator_query_params -q` - 2 passed.
- `python3 -m pytest tests/test_alert_webhook_url.py --cov=jedi_devproject.alert_webhook_url --cov-report=term-missing -q` - 38 passed, 95.56% focused coverage.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 285 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1489 passed, 93.93% coverage.
