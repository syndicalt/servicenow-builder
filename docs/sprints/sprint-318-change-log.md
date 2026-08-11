# Sprint 318 Change Log - Public Web CSV Empty Item Guard

## Summary

- Public-web allowlist and documentation URL CSV parsing now rejects empty items.
- Values with doubled commas or trailing commas fail settings loading instead of silently dropping the empty token.
- Valid comma-separated public-web controls still load unchanged.
- Existing padded CSV, dormant unsafe public-web config, and public-web allowlist validation remain intact.
- Malformed CSV diagnostics name the setting and do not echo the configured CSV value.
- Documented the empty CSV item contract in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_empty_public_web_csv_items_from_env -q` - 2 tests failed before implementation because empty CSV tokens were silently accepted.
- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_reads_public_web_worker_controls tests/test_runtime.py::test_load_runtime_settings_rejects_padded_public_web_csv_values_from_env tests/test_runtime.py::test_load_runtime_settings_rejects_empty_public_web_csv_items_from_env tests/test_runtime.py::test_load_runtime_settings_rejects_dormant_unsafe_public_web_config -q` - 7 passed after implementation.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py` - no issues found in 2 source files.
- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_reads_public_web_worker_controls tests/test_runtime.py::test_load_runtime_settings_rejects_padded_public_web_csv_values_from_env tests/test_runtime.py::test_load_runtime_settings_rejects_empty_public_web_csv_items_from_env tests/test_runtime.py::test_load_runtime_settings_rejects_dormant_unsafe_public_web_config tests/test_project_docs.py::test_sprint_three_hundred_eighteen_documents_public_web_csv_empty_item_guard -q` - 8 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 392 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1910 passed, total coverage 93.87%.
