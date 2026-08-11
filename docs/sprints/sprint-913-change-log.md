# Sprint 913 Change Log - Packet-intent normalized text exact-string guard

## Scope

- Hardened `_optional_intent_text()` normalized text parsing.
- Added a failing-first regression for hostile stringification in shared normalized text handling.
- Documented the normalized-intent exact-string text contract in the operator guide.

## Production Hardening

- Normalized intent text values must be missing or exact strings before deterministic candidate changes are derived.
- String subclasses and arbitrary objects are rejected with the fixed diagnostic `normalized intent text values must be exact strings`.
- The parser does not call `str()` or `repr()` on rejected normalized text values, preventing caller-controlled methods from running during candidate construction, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_catalog_changes_reject_hostile_normalized_text_without_leak`.
- Added `test_sprint_913_documents_packet_intent_normalized_text_guard`.
- Captured 1 failing-first normalized text stringification assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 80 tests.
- Project documentation tests passed: 986 tests.
- Ruff passed for `src` and `tests`.
- Mypy passed for `src` and `tests`.
- Full coverage passed: 3536 tests at 93.54% coverage.
