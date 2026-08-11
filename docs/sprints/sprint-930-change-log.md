# Sprint 930 Change Log - Implementation packet raw payload scalar-subclass boundary

## Scope

- Hardened `_ensure_packet_raw_payload_json_safe()` for normalized-intent raw packet scalar values.
- Added a failing-first regression for hostile scalar-subclass values in raw implementation packet payloads.
- Documented the exact JSON scalar boundary for `_packet_raw_payload()`.

## Production Hardening

- `_packet_raw_payload()` accepts exact strings, exact booleans, exact integers, finite floats, nulls, arrays, tuples, and mappings with exact string keys.
- Boolean and integer subclasses are rejected with the fixed `implementation packet raw payload contains non-JSON values` diagnostic before packet assembly, provider prompting, artifact persistence, or story writeback.
- Raw packet payload diagnostics do not echo normalized-intent field names, operator feedback, story identifiers, object type names, credential-like keys, or payload values.

## Tests

- Added `test_packet_raw_payload_rejects_scalar_subclass_without_payload_leak`.
- Added `test_sprint_930_documents_packet_raw_payload_scalar_subclass_boundary`.
- Captured 1 failing-first implementation packet scalar-subclass assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 84 tests.
- Project documentation tests passed: 1003 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3570 tests at 93.53% total coverage.
