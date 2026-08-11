# Sprint 916 Change Log - Packet-intent client script rendering exact-value guard

## Scope

- Hardened `_catalog_client_script_changes()` downstream rendering of normalized catalog client script dictionaries.
- Added a failing-first regression for hostile stringification in client script name rendering.
- Documented the downstream client script exact-value rendering contract in the operator guide.

## Production Hardening

- Catalog client script rendering values must already be exact normalized strings before candidate changes are emitted.
- Arbitrary objects and string subclasses are rejected with fixed diagnostics such as `catalog client script name must be an exact string`.
- The renderer does not call `str()` or `repr()` on rejected script name, watched variable, or script type values, preventing caller-controlled methods from running during candidate construction, JavaScript rendering, downstream XML generation, ServiceNow handoff, or story writeback.

## Tests

- Added `test_catalog_client_script_renderer_rejects_hostile_name_without_leak`.
- Added `test_sprint_916_documents_packet_intent_client_script_render_guard`.
- Captured 1 failing-first client script renderer stringification assertion.
- Focused sprint tests passed: 2 tests.
- Implementation packet tests passed: 83 tests.
- Project documentation tests passed: 989 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3542 tests at 93.53% total coverage.
