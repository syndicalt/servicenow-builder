# Sprint 923 Change Log - Catalog UI Policy scalar-subclass guard

## Scope

- Hardened `_catalog_ui_policy_field_text()` for Catalog UI Policy customer-update values.
- Added a failing-first regression for hostile scalar-subclass Catalog UI Policy fields.
- Documented the exact JSON scalar boundary for catalog form-behavior rendering.

## Production Hardening

- Catalog UI Policy customer-update rendering accepts exact strings, exact booleans, exact integers, and nulls.
- Boolean and integer subclasses are rejected with the fixed `Catalog UI Policy generation field contains non-JSON value` diagnostic before string conversion.
- The renderer does not call caller-controlled `__str__` methods on scalar subclasses while resolving policy names, matching actions, validating catalog variables, rendering XML, preparing ServiceNow import payloads, or writing story diagnostics.

## Tests

- Added `test_catalog_ui_policy_customer_updates_rejects_scalar_subclass_field_without_leak`.
- Added `test_sprint_923_documents_catalog_ui_policy_scalar_subclass_guard`.
- Captured 1 failing-first Catalog UI Policy scalar-subclass stringification assertion.
- Focused sprint tests passed: 2 tests.
- Generation validator tests passed: 70 tests.
- Project documentation tests passed: 996 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3556 tests at 93.53% total coverage.
