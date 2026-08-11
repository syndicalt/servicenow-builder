# Sprint 909 Change Log - Packet-intent catalog UI Policy reverse_if_false boolean guard

## Scope

- Hardened `_catalog_item_changes_from_normalized_intent()` catalog UI Policy `reverse_if_false` parsing.
- Added a failing-first regression for hostile truthiness in normalized catalog UI Policy rule booleans.
- Documented the normalized-intent `reverse_if_false` exact-boolean contract in the operator guide.

## Production Hardening

- Catalog UI Policy `reverse_if_false` values must be missing or exact booleans before deterministic candidate changes are derived.
- Arbitrary objects are rejected with the fixed diagnostic `catalog variable rule Show schedule reverse_if_false must be a boolean`.
- The parser does not call `bool()`, `str()`, or `repr()` on rejected `reverse_if_false` values, preventing caller-controlled methods from running during candidate construction, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_catalog_changes_reject_hostile_rule_reverse_if_false_without_leak`.
- Added `test_sprint_909_documents_packet_intent_catalog_ui_policy_reverse_guard`.
- Captured 1 failing-first catalog UI Policy reverse_if_false truthiness assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 76 tests.
- Project documentation tests passed: 982 tests.
- Ruff passed for `src` and `tests`.
- Mypy passed for `src` and `tests`.
- Full coverage passed: 3528 tests at 93.52% coverage.
