# Sprint 212 Change Log

Scope: Production hardening - alert webhook double-encoded query separator sensitive-key guard.

## Changes

- Added regression coverage for alert webhook URLs that hide sensitive query keys behind double-encoded ampersand separators such as `team=platform%2526token=secret`.
- Added regression coverage for double-encoded semicolon separators such as `team=platform%253Bclient_secret=secret`.
- Added positive coverage showing benign double-encoded separator values such as `note=fish%2526chips` remain allowed.
- Extended shared alert webhook URL validation so query separator inspection decodes iteratively up to a bounded three-pass limit before startup validation or delivery-time transport invocation.
- Documented bounded double-encoded query separator sensitive-key rejection in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py -q` - 41 passed.
- `python3 -m pytest tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_double_encoded_separator_sensitive_query_parameter tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_double_encoded_separator_query_params -q` - 2 passed.
- `python3 -m pytest tests/test_alert_webhook_url.py --cov=jedi_devproject.alert_webhook_url --cov-report=term-missing -q` - 41 passed, 95.21% focused coverage.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 286 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1495 passed, 93.93% coverage.
