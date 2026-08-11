# Sprint 313 Change Log - Runtime Store and Audit Load Guard

## Summary

- Runtime settings loading now validates required `DATABASE_URL` and `JEDI_AUDIT_ROOT` values before returning `RuntimeSettings`.
- `DATABASE_URL` must be a PostgreSQL URL without raw whitespace/control characters, encoded whitespace/control characters, or URL fragments.
- `JEDI_AUDIT_ROOT` must be an absolute path without whitespace or control characters.
- Production startup validation now reuses the same value-level store and audit checks, preserving fail-closed production behavior.
- Malformed diagnostics name only `DATABASE_URL` or `JEDI_AUDIT_ROOT` and do not echo database credentials or path fragments.
- Added failing regressions proving non-PostgreSQL database URLs, database URL fragments, encoded control characters, relative audit roots, padded audit roots, and control-character audit roots were previously accepted during runtime settings loading.
- Documented the runtime store and audit load guard in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_store_and_audit_values -q` - 6 tests failed before implementation because malformed store and audit values were accepted during runtime settings loading.
- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_store_and_audit_values tests/test_runtime.py::test_load_runtime_settings_accepts_env_file tests/test_runtime.py::test_validate_runtime_settings_rejects_non_postgres_production_database_url tests/test_runtime.py::test_validate_runtime_settings_rejects_production_database_url_fragments tests/test_runtime.py::test_validate_runtime_settings_rejects_relative_audit_root_in_production -q` - 10 passed after implementation.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py` - no issues found in 2 source files.
- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_store_and_audit_values tests/test_project_docs.py::test_sprint_three_hundred_thirteen_documents_runtime_store_audit_load_guard -q` - 7 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 387 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1873 passed, total coverage 93.91%.
