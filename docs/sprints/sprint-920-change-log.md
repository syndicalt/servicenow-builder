# Sprint 920 Change Log - Client Script scalar-subclass guard

## Scope

- Hardened `_client_script_field_text()` for Client Script customer-update values.
- Added a failing-first regression for hostile scalar-subclass Client Script fields.
- Documented the exact JSON scalar boundary for browser-side Client Script rendering.

## Production Hardening

- Client Script customer-update rendering accepts exact strings, exact booleans, exact integers, and nulls.
- Boolean and integer subclasses are rejected with the fixed `Client Script generation field contains non-JSON value` diagnostic before string conversion.
- The renderer does not call caller-controlled `__str__` methods on scalar subclasses while resolving script fields, validating watched fields, scanning script behavior, rendering XML, preparing ServiceNow import payloads, or writing story diagnostics.

## Tests

- Added `test_client_script_customer_updates_rejects_scalar_subclass_field_without_leak`.
- Added `test_sprint_920_documents_client_script_scalar_subclass_guard`.
- Captured 1 failing-first Client Script scalar-subclass stringification assertion.
- Focused sprint tests passed: 2 tests.
- Generation validator tests passed: 67 tests.
- Project documentation tests passed: 993 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3550 tests at 93.53% total coverage.
