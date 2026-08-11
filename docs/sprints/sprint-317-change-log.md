# Sprint 317 Change Log - Fixed ASCII Float Token Guard

## Summary

- Runtime and worker float environment values now share a strict numeric parser.
- Timeout, sleep, retention-prune, and stale-requeue interval values must be fixed ASCII decimal numbers.
- Python float conveniences such as signs, underscores, exponent notation, and non-ASCII decimal digits are rejected instead of being silently normalized.
- Existing padding/control-character and non-finite diagnostics remain intact.
- Malformed float diagnostics name the setting and do not echo the configured numeric fragment.
- Documented the fixed ASCII decimal contract in the operator guide.

## Verification

- `python3 -m pytest tests/test_numeric_settings.py tests/test_runtime.py::test_load_runtime_settings_rejects_non_ascii_fixed_decimal_float_values -q` - failed before implementation because the shared parser did not exist.
- `python3 -m pytest tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_ascii_fixed_decimal_worker_float_values -q` - failed before worker integration because `JEDI_WORKER_IDLE_SLEEP_SECONDS=1_000.5` was accepted.
- `python3 -m pytest tests/test_numeric_settings.py tests/test_runtime.py::test_load_runtime_settings_rejects_non_ascii_fixed_decimal_float_values tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_runtime_float_values tests/test_runtime.py::test_load_runtime_settings_rejects_non_finite_runtime_float_values tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_ascii_fixed_decimal_worker_float_values tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_finite_worker_float_values tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_malformed_worker_numeric_values -q` - 29 passed after implementation.
- `python3 -m ruff check src/jedi_devproject/numeric_settings.py src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_worker.py tests/test_numeric_settings.py tests/test_runtime.py tests/test_runtime_worker_retention.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/numeric_settings.py src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_worker.py tests/test_numeric_settings.py tests/test_runtime.py tests/test_runtime_worker_retention.py` - no issues found in 6 source files.
- `python3 -m pytest tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_positive_stale_requeue_interval tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_ascii_fixed_decimal_worker_float_values tests/test_numeric_settings.py -q` - 20 passed after aligning non-positive coverage to `0` while signed tokens remain strict-token failures.
- `python3 -m ruff check src/jedi_devproject/numeric_settings.py src/jedi_devproject/runtime_worker.py tests/test_runtime_worker_retention.py tests/test_numeric_settings.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/numeric_settings.py src/jedi_devproject/runtime_worker.py tests/test_runtime_worker_retention.py tests/test_numeric_settings.py` - no issues found in 4 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 391 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1907 passed, total coverage 93.86%.
