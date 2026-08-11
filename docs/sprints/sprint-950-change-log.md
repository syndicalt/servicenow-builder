# Sprint 950 Change Log - Business Rule list-subclass guard

## Scope

- Hardened `_business_rule_string_list()` so Business Rule customer-update generation accepts only exact lists before declared field access metadata iteration.
- Documented the Business Rule list-subclass boundary in the operator guide.

## Production Hardening

- List subclasses now fail with `Business Rule generation field contains non-JSON value` before iteration.
- Business Rule generation no longer allows caller-controlled list iterators to run while deriving fields read or fields written metadata.
- Exact list inputs remain supported for declared `fields_read` and `fields_written` metadata.

## Tests

- Added `test_business_rule_customer_updates_rejects_list_subclass_field_without_leak`.
- Captured 1 failing-first Business Rule list-subclass iteration assertion.
- Focused verification passed: 2 tests.
- Scoped verification passed: `tests/test_generation_validators.py` 73 tests and `tests/test_project_docs.py` 1023 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3624 tests at 93.28% coverage.
