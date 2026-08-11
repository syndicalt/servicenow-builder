# Sprint 469 Change Log

## Flow graph round-trip state hash non-finite number rejection

Hardened Flow Designer round-trip graph hashing so UAT provenance cannot be minted over non-strict
JSON containing `NaN`, `Infinity`, or `-Infinity`. `flow_graph_state_hash()` depends on each
`FlowGraphNodeState.canonical()` string as byte-stable evidence for before/after Flow graph state,
so a corrupted node object must fail closed instead of producing a stable-looking digest over
Python-only JSON tokens.

`FlowGraphNodeState.canonical()` now serializes with strict JSON numeric handling before the graph
hash is computed. Non-finite node state fails with
`Flow graph node canonical state contains non-finite numeric values`. The diagnostic is stable and
does not echo node field names or values.

## Verification

- Added 1 failing-first Flow round-trip test covering non-finite node state rejection before graph
  hashing, without field-name or value reflection.
- `python3 -m pytest tests/test_flow_roundtrip.py::test_flow_graph_state_hash_rejects_non_finite_node_state_without_payload_leak -q`:
  failed before implementation because the graph hash accepted the non-finite node state.
- `python3 -m pytest tests/test_flow_roundtrip.py::test_flow_graph_state_hash_rejects_non_finite_node_state_without_payload_leak tests/test_flow_roundtrip.py::test_roundtrip_report_is_deterministic_across_runs tests/test_flow_roundtrip.py::test_roundtrip_add_action_passes_with_committed_post_diff_graph -q`:
  3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 543 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2380 total tests passed at 93.84% coverage.
