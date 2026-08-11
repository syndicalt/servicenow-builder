# Sprint 254 Change Log - Runtime Enum Parsing Hygiene

## Summary

- Runtime enum parsing hygiene prevents malformed enum environment values from surfacing raw model validation errors or losing the setting name.
- Added a runtime settings regression test for malformed values across `JEDI_ADMIN_AUTH_MODE`, `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE`, and `JEDI_PUBLIC_WEB_ACCESS`.
- Added named enum parsing before `RuntimeSettings` construction so invalid enum values raise `RuntimeConfigError` with the setting name and allowed values.
- Documented the accepted runtime enum values and the stable settings-load failure contract.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_runtime_enum_values tests/test_runtime.py::test_load_runtime_settings_reads_admin_console_credentials tests/test_runtime.py::test_load_runtime_settings_defaults_admin_console_auth_disabled tests/test_runtime.py::test_load_runtime_settings_reads_lifecycle_webhook_hmac_config tests/test_runtime.py::test_load_runtime_settings_reads_public_web_worker_controls -q` - 7 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success with 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 328 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1636 passed with 93.96% total coverage.
