# Sprint 467 Change Log

## Flow graph diff validator non-finite number rejection

Hardened Flow Designer graph diff validation so candidate customer-update records and graph payload
safety scans cannot accept non-strict JSON containing `NaN`, `Infinity`, or `-Infinity`. These
validators protect the Flow builder boundary by scanning for raw XML and forbidden capabilities, so
they must fail closed before planning, builder readiness, or retrieved Update Set handoff logic sees
malformed numeric payloads.

Flow graph diff validation now serializes customer-update records and the Python-mode graph payload
with strict JSON numeric handling before safety scanning. Non-finite customer-update values fail with
`Flow graph diff contains a non-finite customer update value`; non-finite graph payload values fail
with `Flow graph diff contains a non-finite payload value`. Both diagnostics are stable and do not
echo malformed field names or values.

## Verification

- Added 2 failing-first Flow graph diff validator tests covering non-finite customer-update records
  and graph payload values without field-name or value reflection.
- `python3 -m pytest tests/test_generation_validators.py::test_flow_graph_diff_rejects_non_finite_customer_updates_without_leak tests/test_generation_validators.py::test_flow_graph_diff_validator_rejects_non_finite_graph_payload_without_leak -q`:
  failed before implementation because both non-finite candidate payloads passed validation.
- `python3 -m pytest tests/test_generation_validators.py::test_flow_graph_diff_validator_rejects_forbidden_flow_tokens tests/test_generation_validators.py::test_flow_graph_diff_rejects_non_finite_customer_updates_without_leak tests/test_generation_validators.py::test_flow_graph_diff_validator_rejects_non_finite_graph_payload_without_leak -q`:
  3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 541 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2376 total tests passed at 93.84% coverage.
