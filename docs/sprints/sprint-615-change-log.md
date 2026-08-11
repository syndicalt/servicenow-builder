# Sprint 615 Change Log

## Model fulfillment artifact exact-string boundary

Sprint 615 continued production hardening by requiring exact string values before model fulfillment artifacts are returned as DB-ready JSON payloads. `_model_artifact_payload()` already rejected non-finite numeric values and unsupported non-JSON values, but string subclasses still passed the model artifact payload preflight and could be serialized as ordinary strings.

`_ensure_model_artifact_payload_json_safe()` now accepts exact `str` values and exact `str` mapping keys only. String subclasses fail through the same `model fulfillment artifact payload contains non-JSON values` diagnostic as other unsupported values, without echoing candidate field names, generated values, story identifiers, object output, credential-like keys, or payload values.

Verification:

- Added 1 failing-first model fulfillment test proving a string subclass model artifact payload value was accepted before implementation.
- `python3 -m pytest tests/test_model_fulfillment.py::test_model_artifact_payload_rejects_string_subclass_candidate_fields_without_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_model_fulfillment.py -q`: 31 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 689 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2710 tests passed at 93.11% coverage.
