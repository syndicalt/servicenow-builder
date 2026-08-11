# Sprint 897 Change Log

## UI Policy generation string-subclass guard

Hardened UI Policy customer-update generation so policy names, target tables, conditions, descriptions, views, flags, order values, action policy names, action tables, action fields, tristate action values, and clear-value flags must use exact JSON-style scalar strings instead of string subclasses.

`ui_policy_customer_updates()` now rejects string subclasses with the fixed `UI Policy generation field contains non-JSON value` diagnostic. The diagnostic does not echo subclass names, overridden string method output, credential-like fragments, conditions, descriptions, view names, or action field values.

This keeps the boundary closed before policy/action matching, tristate validation, forbidden-token scanning, integer parsing, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

## Tests

- Added 1 failing-first UI Policy string-subclass assertion: `test_ui_policy_customer_updates_rejects_string_subclass_field_without_leak`.
- Focused red: `pytest tests/test_generation_validators.py::test_ui_policy_customer_updates_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_897_documents_ui_policy_generation_string_subclass_guard -q` failed because the string subclass executed its overridden `strip()` method before validation failed.
- Focused green: `pytest tests/test_generation_validators.py::test_ui_policy_customer_updates_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_897_documents_ui_policy_generation_string_subclass_guard -q` passed with 2 tests.
- Generation validator suite: `pytest tests/test_generation_validators.py -q` passed with 64 tests.
- Documentation suite: `pytest tests/test_project_docs.py -q` passed with 970 tests.
- Static gates: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3504 tests at 93.52% coverage.
