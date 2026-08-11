# Sprint 899 Change Log

## Catalog Client Script generation string-subclass guard

Hardened Catalog Client Script customer-update generation so catalog item names, script names, script types, watched variables, script bodies, declared fields read, and declared fields written must use exact JSON-style scalar strings instead of string subclasses.

`catalog_client_script_customer_updates()` now rejects string subclasses with the fixed `Catalog Client Script generation field contains non-JSON value` diagnostic. The diagnostic does not echo subclass names, overridden string method output, credential-like fragments, script bodies, variable names, or field metadata.

This keeps the boundary closed before script type validation, script safety scanning, field-write validation, catalog variable ownership checks, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

## Tests

- Added 1 failing-first Catalog Client Script string-subclass assertion: `test_catalog_client_script_rejects_string_subclass_field_without_leak`.
- Focused red: `pytest tests/test_catalog_client_script_generation.py::test_catalog_client_script_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_899_documents_catalog_client_script_generation_string_subclass_guard -q` failed because the string subclass was accepted instead of rejected.
- Focused green: `pytest tests/test_catalog_client_script_generation.py::test_catalog_client_script_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_899_documents_catalog_client_script_generation_string_subclass_guard -q` passed with 2 tests.
- Catalog Client Script suite: `pytest tests/test_catalog_client_script_generation.py -q` passed with 23 tests.
- Documentation suite: `pytest tests/test_project_docs.py -q` passed with 972 tests.
- Static gates: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3508 tests at 93.52% coverage.
