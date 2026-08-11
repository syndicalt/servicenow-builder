# Sprint 255 Change Log - Runtime Environment Mode Guard

## Summary

- Runtime environment mode guarding prevents misspelled `JEDI_ENVIRONMENT` values from silently skipping production validation.
- Added runtime settings regressions for malformed environment values and mixed-case production values.
- Updated settings loading so `JEDI_ENVIRONMENT` accepts only `development` or `production`, normalizes valid values to lowercase, and raises `RuntimeConfigError` naming `JEDI_ENVIRONMENT` for malformed values.
- Documented `JEDI_ENVIRONMENT` as a strict runtime mode switch rather than free-form deployment metadata.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_runtime_environment tests/test_runtime.py::test_load_runtime_settings_normalizes_runtime_environment_case tests/test_runtime.py::test_validate_runtime_settings_rejects_production_without_admin_auth tests/test_runtime.py::test_validate_runtime_settings_rejects_non_postgres_production_database_url -q` - 4 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py` - all checks passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success with 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 329 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1639 passed with 93.96% total coverage.
