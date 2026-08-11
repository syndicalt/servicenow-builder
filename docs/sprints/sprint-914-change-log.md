# Sprint 914 Change Log - Packet-intent normalized order exact-integer guard

## Scope

- Hardened `_optional_intent_order()` normalized order parsing.
- Added a failing-first regression for hostile integer coercion in shared normalized order handling.
- Documented the normalized-intent positive integer order contract in the operator guide.

## Production Hardening

- Normalized intent order values must be missing or exact positive integers before deterministic candidate changes are derived.
- Booleans, strings, arbitrary objects, non-positive integers, and integer subclasses are rejected with the fixed diagnostic `normalized intent order values must be positive integers`.
- The parser does not call `int()`, `str()`, or `repr()` on rejected normalized order values, preventing caller-controlled methods from running during candidate construction, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_catalog_changes_reject_hostile_normalized_order_without_leak`.
- Added `test_sprint_914_documents_packet_intent_normalized_order_guard`.
- Captured 1 failing-first normalized order integer-coercion assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 81 tests.
- Project documentation tests passed: 987 tests.
- Ruff passed for `src` and `tests`.
- Mypy passed for `src` and `tests`.
- Full coverage passed: 3538 tests at 93.55% coverage.
