# Sprint 895 Change Log

## Script Include generation string-subclass guard

Hardened Script Include customer-update generation so Script Include name, API name, scope, callable/active flags, description, script body, public methods, table access metadata, and field access metadata must use exact JSON-style scalar strings instead of string subclasses.

`script_include_customer_updates()` now rejects string subclasses with the fixed `Script Include generation field contains non-JSON value` diagnostic. The diagnostic does not echo subclass names, overridden string method output, credential-like fragments, generated scripts, method names, or access metadata.

This keeps the boundary closed before script safety scanning, scope normalization, method extraction, DTO validation, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

## Tests

- Added 1 failing-first Script Include string-subclass assertion: `test_script_include_customer_updates_rejects_string_subclass_field_without_leak`.
- Focused red: `pytest tests/test_generation_validators.py::test_script_include_customer_updates_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_895_documents_script_include_generation_string_subclass_guard -q` failed because the string subclass was accepted instead of rejected.
- Focused green: `pytest tests/test_generation_validators.py::test_script_include_customer_updates_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_895_documents_script_include_generation_string_subclass_guard -q` passed with 2 tests.
- Generation validator suite: `pytest tests/test_generation_validators.py -q` passed with 62 tests.
- Documentation suite: `pytest tests/test_project_docs.py -q` passed with 968 tests.
- Static gates: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3500 tests at 93.52% coverage.
