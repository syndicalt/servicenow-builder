# Sprint 912 Change Log - Packet-intent fulfillment flow attachment flag guard

## Scope

- Hardened `_catalog_item_changes_from_normalized_intent()` fulfillment flow attachment flag parsing.
- Added a failing-first regression for hostile truthiness in normalized fulfillment flow attachment flags.
- Documented the normalized-intent fulfillment flow attachment exact-boolean contract in the operator guide.

## Production Hardening

- `fulfillment_flow_attachment_requested` values must be missing or exact booleans before deterministic candidate changes are derived.
- Arbitrary objects are rejected with the fixed diagnostic `catalog item fulfillment_flow_attachment_requested must be a boolean`.
- The parser does not call `bool()`, `str()`, or `repr()` on rejected attachment flags, preventing caller-controlled methods from running during candidate construction, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_catalog_changes_reject_hostile_fulfillment_flow_attachment_flag_without_leak`.
- Added `test_sprint_912_documents_packet_intent_fulfillment_flow_attachment_flag_guard`.
- Captured 1 failing-first fulfillment flow attachment flag truthiness assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 79 tests.
- Project documentation tests passed: 985 tests.
- Ruff passed for `src` and `tests`.
- Mypy passed for `src` and `tests`.
- Full coverage passed: 3534 tests at 93.53% coverage.
