# Sprint 944 Change Log - Shared generation-helper container and numeric subclass boundaries

## Scope

- Hardened `string_list()` so generation helper list input accepts only exact lists before item iteration.
- Hardened `reference_value()` so reference dictionaries accept only exact dictionaries before value lookup.
- Hardened `_scalar_text()` so finite float and Decimal conversion accepts only exact `float` and `Decimal` values before string conversion.
- Documented shared generation-helper container and numeric subclass boundaries in the operator guide.

## Production Hardening

- List subclasses now fail with `generation field scalar value contains non-JSON value` before iteration.
- Dictionary subclasses now fail with `generation field scalar value contains non-JSON value` before lookup.
- Float and Decimal subclasses now fail with `generation field scalar value contains non-JSON value` before string conversion.
- Exact primitive JSON-like scalar values and exact supported containers remain supported for deterministic generation helpers.

## Tests

- Added `test_string_list_rejects_list_subclass_without_iteration_leak`.
- Added `test_scalar_text_rejects_float_and_decimal_subclasses_without_stringification`.
- Added `test_reference_value_rejects_dict_subclass_without_lookup_leak`.
- Captured 3 failing-first shared generation-helper subclass assertions.
- Focused verification passed: 4 tests.
- Scoped verification passed: `tests/test_validation_helpers.py` 30 tests and `tests/test_project_docs.py` 1017 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3611 tests at 93.25% coverage.
