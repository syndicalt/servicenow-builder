# Sprint 343 Change Log

Scope: Production hardening - local env and TOML regular-file enforcement.

## Summary

- Local `.env` loading now uses the shared descriptor-safe regular-file reader instead of direct `Path.open()`.
- Project TOML config loading now uses the same regular-file reader before TOML decoding.
- Symlinked or non-regular `.env` paths fail with `dotenv_must_be_regular_file`; symlinked or non-regular TOML paths fail with `project_config_must_be_regular_file`.
- Existing 1 MiB input caps and existing malformed-value diagnostics are preserved.

## Verification

- `python3 -m pytest tests/test_config.py::test_load_config_rejects_symlinked_toml tests/test_servicenow.py::test_load_dotenv_values_rejects_symlinked_env_file -q` - 2 tests failed before implementation because symlinked `.env` and TOML inputs were accepted.
- `python3 -m pytest tests/test_config.py tests/test_servicenow.py::test_load_dotenv_values_rejects_symlinked_env_file tests/test_servicenow.py::test_load_dotenv_values_rejects_oversized_env_without_whole_file_text_read tests/test_servicenow.py::test_load_dotenv_values_reads_expected_keys_without_required_dependency -q` - 15 passed after implementation.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_forty_three_documents_env_toml_regular_file_input tests/test_config.py tests/test_servicenow.py::test_load_dotenv_values_rejects_symlinked_env_file tests/test_servicenow.py::test_load_dotenv_values_rejects_oversized_env_without_whole_file_text_read tests/test_servicenow.py::test_load_dotenv_values_reads_expected_keys_without_required_dependency -q` - 16 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 417 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1996 passed, total coverage 93.99%.
