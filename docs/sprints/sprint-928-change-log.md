# Sprint 928 Change Log - Shared generation-field scalar-subclass guard

## Scope

- Hardened shared scalar conversion in `validation_helpers.py`.
- Added a failing-first regression for hostile scalar-subclass generation-field list items.
- Documented the exact JSON scalar boundary used by shared builder helpers.

## Production Hardening

- `bool_value()`, `string_list()`, `optional_int()`, and `reference_value()` accept exact strings, exact booleans, exact integers, finite floats, finite Decimals, and nulls where supported by their existing contracts.
- Boolean and integer subclasses are rejected with the fixed `generation field scalar value contains non-JSON value` diagnostic before string conversion.
- The shared generation-field path does not call caller-controlled `__str__` methods on boolean or integer subclasses while deriving booleans, trimming list items, parsing optional integers, extracting reference values, building downstream customer updates, importing retrieved Update Sets, or writing story diagnostics.

## Tests

- Added `test_string_list_rejects_scalar_subclass_items_without_string_method_execution`.
- Added `test_sprint_928_documents_generation_field_scalar_subclass_guard`.
- Captured 1 failing-first validation-helper scalar-subclass assertion.
- Focused sprint tests passed: 2 tests.
- Validation-helper tests passed: 27 tests.
- Project documentation tests passed: 1001 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3566 tests at 93.53% total coverage.
