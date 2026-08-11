# Sprint 894 Change Log

## Business Rule generation string-subclass guard

Hardened Business Rule customer-update generation so target table, rule name, timing, operation aliases, filter conditions, script body, and declared table/field access metadata must use exact JSON-style scalar strings instead of string subclasses.

`business_rule_customer_updates()` now rejects string subclasses with the fixed `Business Rule generation field contains non-JSON value` diagnostic. The diagnostic does not echo subclass names, overridden string method output, credential-like fragments, generated scripts, filter conditions, or declared access metadata.

This keeps the boundary closed before operation inference, timing normalization, script safety scanning, field-write validation, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

## Tests

- Added 1 failing-first Business Rule string-subclass assertion: `test_business_rule_customer_updates_rejects_string_subclass_field_without_leak`.
- Focused red: `pytest tests/test_generation_validators.py::test_business_rule_customer_updates_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_894_documents_business_rule_generation_string_subclass_guard -q` failed because the string subclass was accepted instead of rejected.
- Focused green: `pytest tests/test_generation_validators.py::test_business_rule_customer_updates_rejects_string_subclass_field_without_leak tests/test_project_docs.py::test_sprint_894_documents_business_rule_generation_string_subclass_guard -q` passed with 2 tests.
- Generation validator suite: `pytest tests/test_generation_validators.py -q` passed with 61 tests.
- Documentation suite: `pytest tests/test_project_docs.py -q` passed with 967 tests.
- Static gates: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3498 tests at 93.52% coverage.
