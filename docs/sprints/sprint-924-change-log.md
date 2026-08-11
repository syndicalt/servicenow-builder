# Sprint 924 Change Log - Record producer scalar-subclass guard

## Scope

- Hardened `_record_producer_field_text()` for Record Producer customer-update values.
- Added a failing-first regression for hostile scalar-subclass Record Producer fields.
- Documented the exact JSON scalar boundary for Record Producer rendering.

## Production Hardening

- Record Producer customer-update rendering accepts exact strings, exact booleans, exact integers, and nulls.
- Boolean and integer subclasses are rejected with the fixed `record producer generation field contains non-JSON value` diagnostic before string conversion.
- The renderer does not call caller-controlled `__str__` methods on scalar subclasses while resolving producer metadata, validating target tables, normalizing mapped-variable fields, rendering XML, preparing ServiceNow import payloads, or writing story diagnostics.

## Tests

- Added `test_record_producer_customer_updates_rejects_scalar_subclass_field_without_leak`.
- Added `test_sprint_924_documents_record_producer_scalar_subclass_guard`.
- Captured 1 failing-first Record Producer scalar-subclass stringification assertion.
- Focused sprint tests passed: 2 tests.
- Record Producer generation tests passed: 19 tests.
- Project documentation tests passed: 997 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3558 tests at 93.53% total coverage.
