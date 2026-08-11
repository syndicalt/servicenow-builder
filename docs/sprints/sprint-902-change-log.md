# Sprint 902 Change Log

## Dictionary/form metadata string-subclass guard

Hardened dictionary/form live metadata consumption so fetched `sys_ui_section` and `sys_ui_element` text values must use exact JSON-style scalar strings instead of string subclasses.

`dictionary_form_customer_updates()` now rejects string subclasses with the fixed `dictionary/form metadata field contains non-JSON value` diagnostic. The diagnostic does not echo subclass names, overridden string method output, credential-like fragments, section values, view values, element names, element sys_ids, positions, or generated form-layout XML.

This keeps the boundary closed before default-view filtering, anchor matching, position normalization, form-layout planning, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods from hostile or corrupted live instance metadata.

## Tests

- Added 1 failing-first dictionary/form metadata string-subclass assertion: `test_generic_dictionary_form_rejects_string_subclass_metadata_without_leak`.
- Focused red: `pytest tests/test_generic_dictionary_form.py::test_generic_dictionary_form_rejects_string_subclass_metadata_without_leak tests/test_project_docs.py::test_sprint_902_documents_dictionary_form_metadata_string_subclass_guard -q` failed because the string subclass executed its overridden `strip()` method during default-view filtering.
- Focused green: `pytest tests/test_generic_dictionary_form.py::test_generic_dictionary_form_rejects_string_subclass_metadata_without_leak tests/test_project_docs.py::test_sprint_902_documents_dictionary_form_metadata_string_subclass_guard -q` passed with 2 tests.
- Dictionary/form suite: `pytest tests/test_generic_dictionary_form.py -q` passed with 8 tests.
- Documentation suite: `pytest tests/test_project_docs.py -q` passed with 975 tests.
- Static gates: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3514 tests at 93.52% coverage.
