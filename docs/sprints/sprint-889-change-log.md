# Sprint 889 Change Log

## Generation field scalar string-subclass guard

- Added 2 failing-first validation-helper string-subclass assertions: `test_bool_value_rejects_string_subclass_without_string_method_execution` and `test_string_list_rejects_string_subclass_items_without_string_method_execution`.
- Shared generation-field scalar text conversion now requires exact strings before boolean normalization, list item trimming, integer parsing, reference extraction, or builder-specific XML generation can reuse the value.

## Verification

- Focused red: `pytest tests/test_validation_helpers.py::test_bool_value_rejects_string_subclass_without_string_method_execution tests/test_validation_helpers.py::test_string_list_rejects_string_subclass_items_without_string_method_execution tests/test_project_docs.py::test_sprint_889_documents_generation_field_scalar_string_subclass_guard -q` failed because string-subclass generation values executed overridden `strip()` methods.
- Focused green: `pytest tests/test_validation_helpers.py::test_bool_value_rejects_string_subclass_without_string_method_execution tests/test_validation_helpers.py::test_string_list_rejects_string_subclass_items_without_string_method_execution tests/test_project_docs.py::test_sprint_889_documents_generation_field_scalar_string_subclass_guard -q` passed with 3 tests.
- Validation-helper suite: `pytest tests/test_validation_helpers.py -q` passed with 26 tests.
- Docs suite: `pytest tests/test_project_docs.py -q` passed with 962 tests.
- Full gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3488 tests and 93.53% total coverage.
- Focused lint: `python3 -m ruff check src/jedi_devproject/validation_helpers.py tests/test_validation_helpers.py` passed.
- Focused type check: `python3 -m mypy src/jedi_devproject/validation_helpers.py tests/test_validation_helpers.py tests/test_project_docs.py` passed.
