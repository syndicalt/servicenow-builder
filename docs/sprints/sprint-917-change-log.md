# Sprint 917 Change Log - Catalog metadata scalar-subclass guard

## Scope

- Hardened `_catalog_field_text()` for catalog item customer-update metadata values.
- Added a failing-first regression for hostile scalar-subclass metadata fetched from ServiceNow context.
- Documented the exact JSON scalar boundary for catalog metadata rendering in the operator guide.

## Production Hardening

- Catalog item metadata rendering accepts exact strings, exact booleans, exact integers, and nulls.
- Boolean and integer subclasses are rejected with the fixed `catalog item generation field contains non-JSON value` diagnostic before string conversion.
- The metadata renderer does not call caller-controlled `__str__` methods on scalar subclasses while filtering active records, matching display values, rendering relationship XML, preparing ServiceNow import payloads, or writing story diagnostics.

## Tests

- Added `test_catalog_item_customer_updates_rejects_hostile_scalar_subclass_metadata`.
- Added `test_sprint_917_documents_catalog_metadata_scalar_subclass_guard`.
- Captured 1 failing-first catalog metadata scalar-subclass stringification assertion.
- Focused sprint tests passed: 2 tests.
- Catalog item generation tests passed: 50 tests.
- Project documentation tests passed: 990 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3544 tests at 93.53% total coverage.
