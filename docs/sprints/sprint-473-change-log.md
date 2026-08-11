# Sprint 473 Change Log

## Implementation packet nested payload non-finite number rejection

Hardened implementation packet assembly so nested Pydantic DTO payloads cannot silently normalize
corrupted in-process values containing `NaN`, `Infinity`, or `-Infinity` before provider prompting,
artifact storage, or downstream audit evidence receives the packet.

`_packet_model_payload()` now preflights Python-mode DTO payloads with strict JSON numeric handling
before returning the established JSON-mode shape for capability assessments, normalized intents,
surface-operation plans, and instance context DTOs. Non-finite nested packet payloads fail with
`implementation packet nested payload contains non-finite numeric values`. The diagnostic is stable
and does not echo assessment fields, story identifiers, generated values, or payload values.

## Verification

- Added 1 failing-first implementation packet test covering a non-finite capability assessment
  value without field-name or value reflection.
- `python3 -m pytest tests/test_implementation_packet.py::test_packet_model_payload_rejects_non_finite_assessment_without_payload_leak -q`:
  failed before implementation because `_packet_model_payload()` did not exist and implementation
  packet assembly used direct JSON-mode dumps.
- `python3 -m pytest tests/test_implementation_packet.py::test_packet_model_payload_rejects_non_finite_assessment_without_payload_leak tests/test_implementation_packet.py::test_build_implementation_packet_contains_grounded_context_and_controls -q`:
  2 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 547 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2389 total tests passed at 93.85% coverage.
