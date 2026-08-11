# Sprint 747 Change Log - Flow graph hash cause boundary

## Scope

Hardened Flow graph round-trip canonical state hashing diagnostics so non-finite node state failures
do not retain unsafe low-level JSON encoder exceptions as public `ValueError` causes.

## Tests First

- Added 1 failing-first Flow graph hash cause assertion:
  - `tests/test_flow_roundtrip.py::test_flow_graph_state_hash_rejects_non_finite_node_state_without_payload_leak`
- Initial failure proved the public `ValueError` retained the JSON encoder cause for:
  - Flow node state with `private_value_marker` and `do-not-echo-this` in the same node payload as a
    non-finite numeric value.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_747_documents_flow_graph_hash_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original JSON encoder causes in `FlowGraphNodeState.canonical()` for non-finite node
  state failures.
- Preserved the existing fixed diagnostic:
  - `Flow graph node canonical state contains non-finite numeric values`
- Documented the Flow graph hash cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_flow_roundtrip.py -q -k "flow_graph_state_hash_rejects_non_finite"`
  failed first with 1 failure.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_747` failed first with 1 failure.
- `python3 -m pytest tests/test_flow_roundtrip.py -q -k "flow_graph_state_hash_rejects_non_finite"`
  passed with 1 test and 15 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_747` passed with 1 test and 820
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_flow_roundtrip.py -q` passed with 16 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3077 tests and 93.33% total coverage.
