# Sprint 316 Change Log - ASCII Integer Token Guard

## Summary

- The shared integer settings parser now requires ASCII base-10 digits only.
- Unicode decimal digits such as full-width `１２` and Arabic-Indic `١٢` are rejected instead of being accepted by Python `int()`.
- Existing signed-token, underscore-token, padding/control-character, empty-default, and non-positive validation behavior remains intact.
- Malformed integer diagnostics name the setting and do not echo the configured numeric fragment.
- Added direct parser regressions proving non-ASCII decimal tokens were previously accepted.
- Documented the ASCII integer-token contract in the operator guide.

## Verification

- `python3 -m pytest tests/test_numeric_settings.py -q` - 4 tests failed before implementation because non-ASCII decimal digits were accepted and the diagnostic did not state ASCII.
- `python3 -m pytest tests/test_numeric_settings.py tests/test_runtime.py::test_load_runtime_settings_rejects_non_decimal_runtime_integer_values tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_decimal_worker_integer_values tests/test_operational_store.py::test_load_retention_policy_rejects_non_decimal_integer_values -q` - 10 passed after implementation.
- `python3 -m ruff check src/jedi_devproject/numeric_settings.py tests/test_numeric_settings.py tests/test_runtime.py tests/test_runtime_worker_retention.py tests/test_operational_store.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/numeric_settings.py tests/test_numeric_settings.py tests/test_runtime.py tests/test_runtime_worker_retention.py tests/test_operational_store.py` - no issues found in 5 source files.
- `python3 -m pytest tests/test_numeric_settings.py tests/test_project_docs.py::test_sprint_three_hundred_sixteen_documents_ascii_integer_token_guard tests/test_project_docs.py::test_sprint_three_hundred_fifteen_documents_base10_integer_token_guard -q` - 8 passed.
- `python3 -m ruff check src/jedi_devproject/numeric_settings.py tests/test_numeric_settings.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/numeric_settings.py tests/test_numeric_settings.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 390 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1889 passed, total coverage 93.91%.
