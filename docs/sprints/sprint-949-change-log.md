# Sprint 949 Change Log - Script Include list-subclass guard

## Scope

- Hardened `_script_include_string_list()` so Script Include customer-update generation accepts only exact lists before public method, table access, or field access metadata iteration.
- Documented the Script Include list-subclass boundary in the operator guide.

## Production Hardening

- List subclasses now fail with `Script Include generation field contains non-JSON value` before iteration.
- Script Include generation no longer allows caller-controlled list iterators to run while deriving public methods, tables read, tables written, fields read, or fields written metadata.
- Exact list inputs remain supported for declared public method and access metadata.

## Tests

- Added `test_script_include_customer_updates_rejects_list_subclass_field_without_leak`.
- Captured 1 failing-first Script Include list-subclass iteration assertion.
- Focused verification passed: 2 tests.
- Scoped verification passed: `tests/test_generation_validators.py` 72 tests and `tests/test_project_docs.py` 1022 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3622 tests at 93.27% coverage.
