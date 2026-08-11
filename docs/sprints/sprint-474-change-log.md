# Sprint 474 Change Log

## Implementation packet raw normalized-intent non-finite number rejection

Hardened implementation packet assembly for already-normalized automation intent dictionaries.
Those raw dict payloads are not Pydantic DTOs, so they need their own strict JSON preflight before
being attached to implementation packets, shipped to provider prompting, or persisted as artifacts.

`_packet_raw_payload()` now rejects raw packet payloads containing `NaN`, `Infinity`, or `-Infinity`
with `implementation packet raw payload contains non-finite numeric values`. The
diagnostic is stable and does not echo normalized-intent field names, operator feedback, story
identifiers, or payload values.

## Verification

- Added 1 failing-first implementation packet test covering a non-finite raw normalized-intent value
  without field-name or value reflection.
- `python3 -m pytest tests/test_implementation_packet.py::test_packet_raw_payload_rejects_non_finite_normalized_intent_without_payload_leak -q`:
  failed before implementation because `_packet_raw_payload()` did not exist and raw normalized
  automation-intent dicts were attached directly to implementation packets.
- `python3 -m pytest tests/test_implementation_packet.py::test_packet_model_payload_rejects_non_finite_assessment_without_payload_leak tests/test_implementation_packet.py::test_packet_raw_payload_rejects_non_finite_normalized_intent_without_payload_leak tests/test_implementation_packet.py::test_build_implementation_packet_contains_grounded_context_and_controls -q`:
  3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 548 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2391 total tests passed at 93.85% coverage.
