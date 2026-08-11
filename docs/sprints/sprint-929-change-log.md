# Sprint 929 Change Log - Stable artifact hash scalar-subclass boundary

## Scope

- Hardened `_ensure_artifact_hash_payload_json_safe()` for artifact hash payload scalar values.
- Added a failing-first regression for hostile scalar-subclass values in provenance hash payloads.
- Documented the exact JSON scalar boundary for `stable_artifact_hash()`.

## Production Hardening

- `stable_artifact_hash()` accepts exact strings, exact booleans, exact integers, finite floats, nulls, arrays, and mappings with exact string keys.
- Boolean and integer subclasses are rejected with the fixed `artifact hash payload contains non-JSON values` diagnostic before canonical JSON serialization or SHA-256 computation.
- The artifact hash path does not mint provenance hashes from Python scalar subclasses whose runtime behavior can diverge from plain JSON primitives, and diagnostics do not echo payload field names, object type names, credential-like keys, or values.

## Tests

- Added `test_stable_artifact_hash_rejects_scalar_subclass_values_without_payload_leak`.
- Added `test_sprint_929_documents_stable_artifact_hash_scalar_subclass_boundary`.
- Captured 1 failing-first artifact hash scalar-subclass assertion.
- Focused sprint tests passed: 2 tests.
- Core model tests passed: 19 tests.
- Project documentation tests passed: 1002 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3568 tests at 93.53% total coverage.
