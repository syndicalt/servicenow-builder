# Sprint 315 Change Log - Base-10 Integer Token Guard

## Summary

- Runtime, worker, and retention integer environment parsing now uses one shared strict parser for optional base-10 integer settings.
- Integer settings must use base-10 digits only; signed values such as `+60` and underscore-separated values such as `128_000` are rejected instead of being accepted by Python `int()`.
- Existing empty-value defaults, padding/control-character rejection, non-finite float rejection, and non-positive numeric validation remain intact.
- Malformed integer diagnostics name the setting and do not echo the configured numeric fragment.
- Added failing regressions proving runtime integer settings, worker integer settings, and retention integer settings previously accepted non-decimal tokens.
- Documented the stricter base-10 digit-only contract in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_non_decimal_runtime_integer_values tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_decimal_worker_integer_values tests/test_operational_store.py::test_load_retention_policy_rejects_non_decimal_integer_values -q` - 4 tests failed before implementation because signed and underscore-separated integer tokens were accepted.
- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_non_decimal_runtime_integer_values tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_runtime_integer_values tests/test_runtime.py::test_load_runtime_settings_rejects_padded_runtime_integer_values tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_decimal_worker_integer_values tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_malformed_worker_numeric_values tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_padded_worker_numeric_values tests/test_operational_store.py::test_load_retention_policy_rejects_non_decimal_integer_values tests/test_operational_store.py::test_load_retention_policy_rejects_padded_numeric_values -q` - 23 passed after implementation.
- `python3 -m ruff check src/jedi_devproject/numeric_settings.py src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_worker.py src/jedi_devproject/operational_store.py tests/test_runtime.py tests/test_runtime_worker_retention.py tests/test_operational_store.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/numeric_settings.py src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_worker.py src/jedi_devproject/operational_store.py tests/test_runtime.py tests/test_runtime_worker_retention.py tests/test_operational_store.py` - no issues found in 7 source files.
- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_non_decimal_runtime_integer_values tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_decimal_worker_integer_values tests/test_operational_store.py::test_load_retention_policy_rejects_non_decimal_integer_values tests/test_project_docs.py::test_sprint_three_hundred_fifteen_documents_base10_integer_token_guard -q` - 5 passed.
- `python3 -m ruff check src/jedi_devproject/numeric_settings.py src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_worker.py src/jedi_devproject/operational_store.py tests/test_runtime.py tests/test_runtime_worker_retention.py tests/test_operational_store.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/numeric_settings.py src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_worker.py src/jedi_devproject/operational_store.py tests/test_runtime.py tests/test_runtime_worker_retention.py tests/test_operational_store.py tests/test_project_docs.py` - no issues found in 8 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 389 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 180 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1882 passed, total coverage 93.91%.
