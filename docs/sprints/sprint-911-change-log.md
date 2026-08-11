# Sprint 911 Change Log - Packet-intent record producer variable mandatory boolean guard

## Scope

- Hardened `_record_producer_changes_from_normalized_intent()` record producer variable `mandatory` parsing.
- Added a failing-first regression for hostile truthiness in normalized record producer variable booleans.
- Documented the normalized-intent record producer variable `mandatory` exact-boolean contract in the operator guide.

## Production Hardening

- Record producer variable `mandatory` values must be missing or exact booleans before deterministic candidate changes are derived.
- Arbitrary objects are rejected with the fixed diagnostic `record producer variable summary mandatory must be a boolean`.
- The parser does not call `bool()`, `str()`, or `repr()` on rejected `mandatory` values, preventing caller-controlled methods from running during candidate construction, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_record_producer_changes_reject_hostile_variable_mandatory_without_leak`.
- Added `test_sprint_911_documents_packet_intent_record_producer_variable_mandatory_guard`.
- Captured 1 failing-first record producer mandatory truthiness assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 78 tests.
- Project documentation tests passed: 984 tests.
- Ruff passed for `src` and `tests`.
- Mypy passed for `src` and `tests`.
- Full coverage passed: 3532 tests at 93.53% coverage.
