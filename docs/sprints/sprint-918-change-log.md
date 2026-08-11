# Sprint 918 Change Log - Catalog client script scalar-subclass guard

## Scope

- Hardened `_catalog_client_script_field_text()` for catalog client script customer-update values.
- Added a failing-first regression for hostile scalar-subclass script fields.
- Documented the exact JSON scalar boundary for catalog client script customer-update rendering.

## Production Hardening

- Catalog client script customer-update rendering accepts exact strings, exact booleans, exact integers, and nulls.
- Boolean and integer subclasses are rejected with the fixed `Catalog Client Script generation field contains non-JSON value` diagnostic before string conversion.
- The renderer does not call caller-controlled `__str__` methods on scalar subclasses while resolving script fields, validating script bodies, rendering XML, preparing ServiceNow import payloads, or writing story diagnostics.

## Tests

- Added `test_catalog_client_script_rejects_scalar_subclass_field_without_leak`.
- Added `test_sprint_918_documents_catalog_client_script_scalar_subclass_guard`.
- Captured 1 failing-first catalog client script scalar-subclass stringification assertion.
- Focused sprint tests passed: 2 tests.
- Catalog client script generation tests passed: 24 tests.
- Project documentation tests passed: 991 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3546 tests at 93.53% total coverage.
