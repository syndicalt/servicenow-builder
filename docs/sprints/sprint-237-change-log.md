# Sprint 237 Change Log

Scope: Production hardening - ServiceNow OAuth credential character hygiene.

## Changes

- Added regression coverage that production validation rejects `SERVICENOW_DEV_CLIENT_SECRET` values containing control characters.
- Added production runtime validation for configured ServiceNow OAuth client IDs and secrets.
- ServiceNow OAuth credential values now must not contain whitespace or control characters in production.
- Documented the production ServiceNow OAuth credential validation rule in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_servicenow_oauth_secret_control_characters -q` - 1 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 311 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1582 passed, 93.91% coverage.
