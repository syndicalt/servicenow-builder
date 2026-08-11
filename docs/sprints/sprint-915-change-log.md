# Sprint 915 Change Log - Packet-intent UI Policy rendering exact-value guard

## Scope

- Hardened `_catalog_ui_policy_changes()` downstream rendering of normalized UI Policy dictionaries.
- Added a failing-first regression for hostile stringification in UI Policy action variable rendering.
- Documented the downstream UI Policy exact-value rendering contract in the operator guide.

## Production Hardening

- Catalog UI Policy rendering values must already be exact normalized strings and booleans before candidate changes are emitted.
- Arbitrary objects and string subclasses are rejected with fixed diagnostics such as `catalog variable rule Show schedule action variable must be an exact string`.
- The renderer does not call `str()`, `bool()`, or `repr()` on rejected rule or action values, preventing caller-controlled methods from running during candidate construction, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_catalog_ui_policy_renderer_rejects_hostile_action_variable_without_leak`.
- Added `test_sprint_915_documents_packet_intent_ui_policy_render_guard`.
- Captured 1 failing-first UI Policy renderer stringification assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 82 tests.
- Project documentation tests passed: 988 tests.
- Ruff passed for `src` and `tests`.
- Mypy passed for `src` and `tests`.
- Full coverage passed: 3540 tests at 93.53% coverage.
