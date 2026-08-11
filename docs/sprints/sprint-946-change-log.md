# Sprint 946 Change Log - Catalog Client Script list-subclass guard

## Scope

- Hardened `_catalog_client_script_string_list()` so Catalog Client Script customer-update generation accepts only exact lists before declared read/write field iteration.
- Documented the Catalog Client Script list-subclass boundary in the operator guide.

## Production Hardening

- List subclasses now fail with `Catalog Client Script generation field contains non-JSON value` before iteration.
- Catalog Client Script generation no longer allows caller-controlled list iterators to run while deriving field-read or field-write metadata.
- Exact list inputs remain supported for declared `fields_read` and `fields_written` metadata.

## Tests

- Added `test_catalog_client_script_rejects_list_subclass_field_without_leak`.
- Captured 1 failing-first Catalog Client Script list-subclass iteration assertion.
- Focused verification passed: 2 tests.
- Scoped verification passed: `tests/test_catalog_client_script_generation.py` 25 tests and `tests/test_project_docs.py` 1019 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3615 tests at 93.25% coverage.
