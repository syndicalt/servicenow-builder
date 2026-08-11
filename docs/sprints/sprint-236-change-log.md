# Sprint 236 Change Log

Scope: Production hardening - ServiceNow instance URL transport hygiene.

## Changes

- Added regression coverage that production validation rejects non-HTTPS `SERVICENOW_DEV_INSTANCE_URL` values.
- Added production runtime validation for configured ServiceNow instance URLs.
- ServiceNow instance URLs now must use HTTPS and must not include embedded credentials, URL fragments, raw or encoded whitespace, or control characters in production.
- Documented the production ServiceNow URL validation rule in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_non_https_servicenow_instance_url -q` - 1 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 310 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1580 passed, 93.91% coverage.
