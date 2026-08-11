# Sprint 1019 Change Log - Validation helper Decimal input guard

## Summary

Hardened shared generation-field scalar normalization so Decimal values are rejected instead of
stringified.

## Security

`_scalar_text()` now accepts only exact strings, booleans, integers, and finite floats. Exact Decimal
values are rejected with `generation field scalar value contains non-JSON value`.

This keeps `bool_value()`, `string_list()`, `optional_int()`, and `reference_value()` aligned with
JSON-like generation field input and prevents arbitrary numeric object families from entering
generation metadata normalization.

## Tests

- Added 1 failing-first optional-int Decimal assertion:
  `test_optional_int_rejects_decimal_without_value_leak`.
- Added 1 failing-first bool-value Decimal assertion:
  `test_bool_value_rejects_decimal_without_value_leak`.
- Added 1 documentation assertion:
  `test_sprint_1019_documents_validation_helper_decimal_input_guard`.

## Verification

- `pytest tests/test_validation_helpers.py::test_optional_int_rejects_decimal_without_value_leak tests/test_validation_helpers.py::test_bool_value_rejects_decimal_without_value_leak -q`
  failed before implementation because Decimal values were accepted.
