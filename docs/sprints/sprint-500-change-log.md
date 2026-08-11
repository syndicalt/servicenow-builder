# Sprint 500 Change Log

## Implementation packet nested DTO non-JSON value rejection

Hardened `_packet_model_payload()` so implementation packet nested DTO conversion cannot fail through raw Pydantic serializer diagnostics when corrupted in-process capability assessments, normalized intents, surface-operation plans, or instance context DTOs contain unsupported Python values.

Sprint 473 rejected non-finite numeric nested packet DTO values. This sprint closes the adjacent structural JSON gap: unsupported objects, bytes, and other non-JSON values now fail before provider prompting, packet return, or artifact persistence with the fixed `implementation packet nested payload contains non-JSON values` diagnostic. The diagnostic does not echo assessment fields, story identifiers, generated values, object type names, object string output, credential-like keys, or payload values.

The implementation preserves valid Pydantic-native nested DTO values by preflighting Python-mode payloads, then returning the established Pydantic JSON-mode packet shape.

## Verification

- Added 1 failing-first implementation packet test proving an object with secret-bearing `__str__` output previously surfaced a raw Pydantic serializer diagnostic.
- `python3 -m pytest tests/test_implementation_packet.py::test_packet_model_payload_rejects_non_json_assessment_without_payload_leak -q`: failed before implementation because the diagnostic reflected the local object type name.
- `python3 -m pytest tests/test_implementation_packet.py::test_packet_model_payload_rejects_non_json_assessment_without_payload_leak tests/test_implementation_packet.py::test_packet_model_payload_rejects_non_finite_assessment_without_payload_leak tests/test_implementation_packet.py::test_model_payload_includes_structured_context_dossier_with_xml_shape_references -q`: 3 tests passed.
- `python3 -m pytest tests/test_implementation_packet.py -q`: 66 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 574 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2443 total tests passed at 93.64% coverage.
