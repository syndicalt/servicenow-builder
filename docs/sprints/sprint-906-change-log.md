# Sprint 906 Change Log - Packet-intent catalog variable set name guard

## Scope

- Hardened `_catalog_item_changes_from_normalized_intent()` catalog variable set name parsing.
- Added a failing-first regression for hostile string subclasses in normalized catalog variable set names.
- Documented the normalized-intent variable set exact-string contract in the operator guide.

## Production Hardening

- Catalog variable set names must be exact strings before deterministic candidate changes are derived.
- String subclasses and arbitrary objects are rejected with the fixed diagnostic `catalog variable set names must be exact strings`.
- The parser does not call `str()` or `repr()` on rejected variable set names, preventing caller-controlled methods from running during candidate construction, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_catalog_changes_reject_string_subclass_variable_set_without_leak`.
- Added `test_sprint_906_documents_packet_intent_catalog_variable_set_name_guard`.
- Captured 1 failing-first catalog variable set string-subclass assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 73 tests.
- Project documentation tests passed: 979 tests.
- Ruff passed for `src` and `tests`.
- Mypy passed for `src` and `tests`.
- Full coverage passed: 3522 tests at 93.51% coverage.
