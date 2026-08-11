# Sprint 921 Change Log - Script Include scalar-subclass guard

## Scope

- Hardened `_script_include_field_text()` for Script Include customer-update values.
- Added a failing-first regression for hostile scalar-subclass Script Include fields.
- Documented the exact JSON scalar boundary for server-side Script Include rendering.

## Production Hardening

- Script Include customer-update rendering accepts exact strings, exact booleans, exact integers, and nulls.
- Boolean and integer subclasses are rejected with the fixed `Script Include generation field contains non-JSON value` diagnostic before string conversion.
- The renderer does not call caller-controlled `__str__` methods on scalar subclasses while resolving Script Include names, normalizing scope, validating callable/active flags, scanning script behavior, rendering XML, preparing ServiceNow import payloads, or writing story diagnostics.

## Tests

- Added `test_script_include_customer_updates_rejects_scalar_subclass_field_without_leak`.
- Added `test_sprint_921_documents_script_include_scalar_subclass_guard`.
- Captured 1 failing-first Script Include scalar-subclass stringification assertion.
- Focused sprint tests passed: 2 tests.
- Generation validator tests passed: 68 tests.
- Project documentation tests passed: 994 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3552 tests at 93.53% total coverage.
