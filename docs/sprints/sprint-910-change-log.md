# Sprint 910 Change Log - Packet-intent catalog variable mandatory boolean guard

## Scope

- Hardened `_catalog_item_changes_from_normalized_intent()` catalog variable `mandatory` parsing.
- Added a failing-first regression for hostile truthiness in normalized catalog variable booleans.
- Documented the normalized-intent catalog variable `mandatory` exact-boolean contract in the operator guide.

## Production Hardening

- Catalog variable `mandatory` values must be missing or exact booleans before deterministic candidate changes are derived.
- Arbitrary objects are rejected with the fixed diagnostic `catalog variable visitor_name mandatory must be a boolean`.
- The parser does not call `bool()`, `str()`, or `repr()` on rejected `mandatory` values, preventing caller-controlled methods from running during candidate construction, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_catalog_changes_reject_hostile_catalog_variable_mandatory_without_leak`.
- Added `test_sprint_910_documents_packet_intent_catalog_variable_mandatory_guard`.
- Captured 1 failing-first catalog variable mandatory truthiness assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 77 tests.
- Project documentation tests passed: 983 tests.
- Ruff passed for `src` and `tests`.
- Mypy passed for `src` and `tests`.
- Full coverage passed: 3530 tests at 93.53% coverage.
