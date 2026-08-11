# Sprint 475 Change Log

## Context dossier DTO payload non-finite number rejection

Hardened context dossier assembly so reusable packet-context code cannot silently normalize
corrupted discovery or surface-context DTOs containing `NaN`, `Infinity`, or `-Infinity`. The
implementation packet already preflights the main packet fields, but `_context_dossier()` is an
internal model-facing boundary and now enforces the same strict JSON numeric handling locally.

`_context_model_payload()` now preflights Python-mode Pydantic DTO payloads before returning the
established JSON-mode shape used inside `context_dossier`. Non-finite dossier DTO payloads fail with
`context dossier DTO payload contains non-finite numeric values`. The diagnostic is stable and does
not echo context field names, ServiceNow evidence values, story identifiers, or payload values.

## Verification

- Added 1 failing-first packet context test covering a non-finite surface context confidence value
  without field-name or value reflection.
- `python3 -m pytest tests/test_packet_context.py::test_context_model_payload_rejects_non_finite_dto_without_payload_leak -q`:
  failed before implementation because `_context_model_payload()` did not exist and context dossier
  assembly used direct JSON-mode dumps.
- `python3 -m pytest tests/test_packet_context.py::test_context_model_payload_rejects_non_finite_dto_without_payload_leak tests/test_implementation_packet.py::test_model_payload_includes_structured_context_dossier_with_xml_shape_references -q`:
  2 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 549 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2393 total tests passed at 93.86% coverage.
