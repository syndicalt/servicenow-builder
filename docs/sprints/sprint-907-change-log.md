# Sprint 907 Change Log - Packet-intent catalog variable group member guard

## Scope

- Hardened `_catalog_item_changes_from_normalized_intent()` catalog variable group member parsing.
- Added a failing-first regression for hostile string subclasses in normalized catalog variable group member names.
- Documented the normalized-intent variable group member exact-string contract in the operator guide.

## Production Hardening

- Catalog variable group member names must be exact strings before deterministic candidate changes are derived.
- String subclasses and arbitrary objects are rejected with the fixed diagnostic `catalog variable group Schedule members must be exact strings`.
- The parser does not call `str()` or `repr()` on rejected group members, preventing caller-controlled methods from running during candidate construction, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_catalog_changes_reject_string_subclass_variable_group_member_without_leak`.
- Added `test_sprint_907_documents_packet_intent_catalog_variable_group_member_guard`.
- Captured 1 failing-first catalog variable group member string-subclass assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 74 tests.
- Project documentation tests passed: 980 tests.
- Ruff passed for `src` and `tests`.
- Mypy passed for `src` and `tests`.
- Full coverage passed: 3524 tests at 93.52% coverage.
