# Sprint 908 Change Log - Packet-intent catalog UI Policy cleared boolean guard

## Scope

- Hardened `_catalog_item_changes_from_normalized_intent()` catalog UI Policy action `cleared` parsing.
- Added a failing-first regression for hostile truthiness in normalized catalog UI Policy action booleans.
- Documented the normalized-intent `cleared` exact-boolean contract in the operator guide.

## Production Hardening

- Catalog UI Policy action `cleared` values must be missing or exact booleans before deterministic candidate changes are derived.
- Arbitrary objects are rejected with the fixed diagnostic `catalog variable rule Show schedule action cleared must be a boolean`.
- The parser does not call `bool()`, `str()`, or `repr()` on rejected `cleared` values, preventing caller-controlled methods from running during candidate construction, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_catalog_changes_reject_hostile_rule_action_cleared_without_leak`.
- Added `test_sprint_908_documents_packet_intent_catalog_ui_policy_cleared_guard`.
- Captured 1 failing-first catalog UI Policy cleared truthiness assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 75 tests.
- Project documentation tests passed: 981 tests.
- Ruff passed for `src` and `tests`.
- Mypy passed for `src` and `tests`.
- Full coverage passed: 3526 tests at 93.52% coverage.
