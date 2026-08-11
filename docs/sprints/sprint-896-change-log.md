# Sprint 896 Change Log

## Client Script generation string-subclass guard

Hardened Client Script customer-update generation so target table, script name, script type, watched field, script body, declared field access metadata, and user-facing message metadata must use exact JSON-style scalar strings instead of string subclasses.

`client_script_customer_updates()` now rejects string subclasses with the fixed `Client Script generation field contains non-JSON value` diagnostic. The diagnostic does not echo subclass names, overridden string method output, credential-like fragments, generated scripts, watched field names, or message text.

This keeps the boundary closed before script type validation, watched-field validation, script safety scanning, field-write validation, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

## Tests

- Added 1 failing-first Client Script string-subclass assertion: `test_client_script_customer_updates_rejects_string_subclass_field_without_leak`.
- Focused red: `pytest tests/test_generation_validators.py::test_client_script_customer_updates_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_896_documents_client_script_generation_string_subclass_guard -q` failed because the string subclass was accepted instead of rejected.
- Focused green: `pytest tests/test_generation_validators.py::test_client_script_customer_updates_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_896_documents_client_script_generation_string_subclass_guard -q` passed with 2 tests.
- Generation validator suite: `pytest tests/test_generation_validators.py -q` passed with 63 tests.
- Documentation suite: `pytest tests/test_project_docs.py -q` passed with 969 tests.
- Static gates: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3502 tests at 93.52% coverage.
