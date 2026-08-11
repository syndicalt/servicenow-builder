# Sprint 498 Change Log

## Model fulfillment artifact non-JSON value rejection

Hardened `_model_artifact_payload()` so DB-ready model fulfillment artifacts cannot fail through raw Pydantic serializer diagnostics when corrupted in-process model objects contain unsupported Python values.

Sprint 472 rejected non-finite numeric model artifact values. This sprint closes the adjacent structural JSON gap: unsupported objects, bytes, and other non-JSON values now fail before context bundle, implementation packet, implementation candidate, or ATF plan artifact payloads are returned for persistence with the fixed `model fulfillment artifact payload contains non-JSON values` diagnostic. The diagnostic does not echo candidate field names, generated values, story identifiers, object type names, object string output, credential-like keys, or payload values.

The implementation preserves valid Pydantic-native artifact values by preflighting Python-mode payloads, then returning the established Pydantic JSON-mode DB-ready artifact shape.

## Verification

- Added 1 failing-first model fulfillment test proving an object with secret-bearing `__str__` output previously surfaced a raw Pydantic serializer diagnostic.
- `python3 -m pytest tests/test_model_fulfillment.py::test_model_artifact_payload_rejects_non_json_candidate_fields_without_leak -q`: failed before implementation because the diagnostic reflected the local object type name.
- `python3 -m pytest tests/test_model_fulfillment.py::test_model_artifact_payload_rejects_non_json_candidate_fields_without_leak tests/test_model_fulfillment.py::test_model_artifact_payload_rejects_non_finite_candidate_fields_without_leak tests/test_model_fulfillment.py::test_model_candidate_handler_returns_packet_candidate_payloads_and_work_note -q`: 3 tests passed.
- `python3 -m pytest tests/test_model_fulfillment.py -q`: 30 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 572 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2439 total tests passed at 93.74% coverage.
