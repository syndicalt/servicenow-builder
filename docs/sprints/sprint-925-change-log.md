# Sprint 925 Change Log - ATF generation scalar-subclass guard

## Scope

- Hardened `_atf_field_text()` for advisory ATF test plan generation values.
- Added a failing-first regression for hostile scalar-subclass ATF candidate fields.
- Documented the exact JSON scalar boundary for ATF test plan rendering.

## Production Hardening

- ATF test plan generation accepts exact strings, exact booleans, exact integers, and nulls.
- Boolean and integer subclasses are rejected with the fixed `ATF test plan generation field contains non-JSON value` diagnostic before string conversion.
- The renderer does not call caller-controlled `__str__` methods on scalar subclasses while parsing operation flags, deriving test scenarios, normalizing steps, building artifact payloads, or writing story diagnostics.

## Tests

- Added `test_atf_test_plan_rejects_scalar_subclass_candidate_field_without_leak`.
- Added `test_sprint_925_documents_atf_generation_scalar_subclass_guard`.
- Captured 1 failing-first ATF scalar-subclass stringification assertion.
- Focused sprint tests passed: 2 tests.
- ATF test generation tests passed: 32 tests.
- Project documentation tests passed: 998 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3560 tests at 93.53% total coverage.
