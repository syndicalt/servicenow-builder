# Sprint 898 Change Log

## Catalog UI Policy generation string-subclass guard

Hardened Catalog UI Policy customer-update generation so policy names, catalog item names, catalog conditions, flags, order values, script placeholders, action policy names, action variables, action tristate values, and clear-value flags must use exact JSON-style scalar strings instead of string subclasses.

`catalog_ui_policy_customer_updates()` now rejects string subclasses with the fixed `Catalog UI Policy generation field contains non-JSON value` diagnostic. The diagnostic does not echo subclass names, overridden string method output, credential-like fragments, catalog conditions, catalog item names, script placeholders, or action variable values.

This keeps the boundary closed before policy/action matching, variable ownership checks, condition parsing, tristate validation, integer parsing, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

## Tests

- Added 1 failing-first Catalog UI Policy string-subclass assertion: `test_catalog_ui_policy_customer_updates_rejects_string_subclass_field_without_leak`.
- Focused red: `pytest tests/test_generation_validators.py::test_catalog_ui_policy_customer_updates_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_898_documents_catalog_ui_policy_generation_string_subclass_guard -q` failed because the string subclass executed its overridden `strip()` method before validation failed.
- Focused green: `pytest tests/test_generation_validators.py::test_catalog_ui_policy_customer_updates_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_898_documents_catalog_ui_policy_generation_string_subclass_guard -q` passed with 2 tests.
- Generation validator suite: `pytest tests/test_generation_validators.py -q` passed with 65 tests.
- Documentation suite: `pytest tests/test_project_docs.py -q` passed with 971 tests.
- Static gates: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3506 tests at 93.52% coverage.
