# Sprint 268 Change Log - Bounded Env File Input

## Summary

- Added a shared `.env` input limit of 1 MiB for ServiceNow, runtime, and worker configuration loading.
- Replaced dotenv `Path.read_text()` parsing with a bounded binary read that rejects oversized files before decode and line parsing.
- Preserved existing dotenv behavior for comments, blank lines, malformed lines, quote stripping, and ServiceNow OAuth key loading.
- Added a failing regression proving oversized dotenv input is rejected without calling `Path.read_text()`.
- Documented the dotenv input cap in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_load_dotenv_values_rejects_oversized_env_without_whole_file_text_read -q` - 1 test failed before implementation because the parser called `Path.read_text()`.
- `python3 -m pytest tests/test_servicenow.py::test_load_dotenv_values_reads_expected_keys_without_required_dependency tests/test_servicenow.py::test_load_dotenv_values_ignores_comments_blanks_and_malformed_lines tests/test_servicenow.py::test_load_dotenv_values_rejects_oversized_env_without_whole_file_text_read -q` - 3 passed.
- `python3 -m pytest tests/test_servicenow.py::test_load_dotenv_values_reads_expected_keys_without_required_dependency tests/test_servicenow.py::test_load_dotenv_values_ignores_comments_blanks_and_malformed_lines tests/test_servicenow.py::test_load_dotenv_values_rejects_oversized_env_without_whole_file_text_read tests/test_project_docs.py::test_sprint_two_hundred_sixty_eight_documents_bounded_env_file_input -q` - 4 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 342 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1671 passed, total coverage 94.00%.
