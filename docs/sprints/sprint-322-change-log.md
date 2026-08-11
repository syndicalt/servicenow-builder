# Sprint 322 Change Log - Runtime Settings Validation Input Redaction

## Summary

- Direct `RuntimeSettings` validation now suppresses rejected input values in Pydantic validation errors.
- Runtime setting type, enum, and parsing failures still name the invalid field without echoing raw rejected configuration.
- The redaction boundary covers direct configuration wiring for database URLs, admin-auth selectors, public-web selectors, numeric settings, and other runtime settings before startup logs or worker failures can reflect untrusted input.
- Existing runtime settings loading and production validation behavior remains intact.
- Documented the runtime settings diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_runtime_settings_validation_errors_do_not_echo_rejected_inputs -q` - 4 tests failed before implementation because direct `RuntimeSettings` validation errors included `input_value`.
- `python3 -m pytest tests/test_runtime.py::test_runtime_settings_validation_errors_do_not_echo_rejected_inputs tests/test_runtime.py -q` - 275 passed after implementation.
- `python3 -m pytest tests/test_runtime.py::test_runtime_settings_validation_errors_do_not_echo_rejected_inputs tests/test_project_docs.py::test_sprint_three_hundred_twenty_two_documents_runtime_settings_error_redaction -q` - 5 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 396 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1933 passed, total coverage 93.87%.
