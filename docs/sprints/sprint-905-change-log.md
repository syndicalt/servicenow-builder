# Sprint 905 Change Log - Packet-intent catalog client script action guard

## Scope

- Hardened `_catalog_item_changes_from_normalized_intent()` catalog client script action parsing.
- Added a failing-first regression for hostile string subclasses in normalized catalog client script action text.
- Documented the normalized-intent client script action exact-string contract in the operator guide.

## Production Hardening

- Catalog client script action `kind`, `variable`, and `value` values must be missing or exact strings before deterministic candidate changes are derived.
- String subclasses and arbitrary objects are rejected with the fixed diagnostic `catalog client script populate_visitor action kind must be an exact string`.
- The parser does not call `str()` or `repr()` on rejected action values, preventing caller-controlled methods from running during candidate construction, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_catalog_changes_reject_string_subclass_client_script_action_without_leak`.
- Added `test_sprint_905_documents_packet_intent_catalog_client_script_action_guard`.
- Captured 1 failing-first catalog client script action string-subclass assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 72 tests.
- Project documentation tests passed: 978 tests.
- Ruff passed for `src` and `tests`.
- Mypy passed for `src` and `tests`.
- Full coverage passed: 3520 tests at 93.51% coverage.
