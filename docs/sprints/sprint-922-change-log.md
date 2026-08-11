# Sprint 922 Change Log - UI Policy scalar-subclass guard

## Scope

- Hardened `_ui_policy_field_text()` for UI Policy customer-update values.
- Added a failing-first regression for hostile scalar-subclass UI Policy fields.
- Documented the exact JSON scalar boundary for declarative UI Policy rendering.

## Production Hardening

- UI Policy customer-update rendering accepts exact strings, exact booleans, exact integers, and nulls.
- Boolean and integer subclasses are rejected with the fixed `UI Policy generation field contains non-JSON value` diagnostic before string conversion.
- The renderer does not call caller-controlled `__str__` methods on scalar subclasses while resolving policy names, matching actions, validating tristate behavior, rendering XML, preparing ServiceNow import payloads, or writing story diagnostics.

## Tests

- Added `test_ui_policy_customer_updates_rejects_scalar_subclass_field_without_leak`.
- Added `test_sprint_922_documents_ui_policy_scalar_subclass_guard`.
- Captured 1 failing-first UI Policy scalar-subclass stringification assertion.
- Focused sprint tests passed: 2 tests.
- Generation validator tests passed: 69 tests.
- Project documentation tests passed: 995 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3554 tests at 93.53% total coverage.
