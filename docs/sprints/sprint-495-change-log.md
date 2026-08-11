# Sprint 495 Change Log

## Context dossier DTO non-JSON value rejection

Hardened `_context_model_payload()` so model-facing context dossier DTO conversion cannot fail through raw Pydantic serializer diagnostics when a corrupted in-process discovery or surface-context DTO contains unsupported Python values.

Sprint 475 rejected non-finite numeric context DTO values. This sprint closes the adjacent structural JSON gap: unsupported objects, bytes, and other non-JSON values now fail before context dossier compaction or model-facing packet output with the fixed `context dossier DTO payload contains non-JSON values` diagnostic. The diagnostic does not echo context field names, ServiceNow evidence values, story identifiers, object type names, object string output, credential-like keys, or payload values.

The implementation preserves valid Pydantic-native DTO values by preflighting Python-mode payloads, then returning the established Pydantic JSON-mode payload shape used inside `context_dossier`.

## Verification

- Added 1 failing-first packet context test proving an object with secret-bearing `__str__` output previously surfaced a raw Pydantic serializer diagnostic.
- `python3 -m pytest tests/test_packet_context.py::test_context_model_payload_rejects_non_json_dto_without_payload_leak -q`: failed before implementation because the diagnostic reflected the local object type name.
- `python3 -m pytest tests/test_packet_context.py::test_context_model_payload_rejects_non_json_dto_without_payload_leak tests/test_packet_context.py::test_context_model_payload_rejects_non_finite_dto_without_payload_leak tests/test_implementation_packet.py::test_model_payload_includes_structured_context_dossier_with_xml_shape_references -q`: 3 tests passed.
- `python3 -m pytest tests/test_packet_context.py -q`: 2 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 569 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2433 total tests passed at 93.75% coverage.
