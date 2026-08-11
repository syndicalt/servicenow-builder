# Sprint 919 Change Log - Business Rule scalar-subclass guard

## Scope

- Hardened `_business_rule_field_text()` for Business Rule customer-update values.
- Added a failing-first regression for hostile scalar-subclass Business Rule fields.
- Documented the exact JSON scalar boundary for server-side Business Rule rendering.

## Production Hardening

- Business Rule customer-update rendering accepts exact strings, exact booleans, exact integers, and nulls.
- Boolean and integer subclasses are rejected with the fixed `Business Rule generation field contains non-JSON value` diagnostic before string conversion.
- The renderer does not call caller-controlled `__str__` methods on scalar subclasses while resolving rule fields, inferring operations, validating server-side script behavior, rendering XML, preparing ServiceNow import payloads, or writing story diagnostics.

## Tests

- Added `test_business_rule_customer_updates_rejects_scalar_subclass_field_without_leak`.
- Added `test_sprint_919_documents_business_rule_scalar_subclass_guard`.
- Captured 1 failing-first Business Rule scalar-subclass stringification assertion.
- Focused sprint tests passed: 2 tests.
- Generation validator tests passed: 66 tests.
- Project documentation tests passed: 992 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3548 tests at 93.53% total coverage.
