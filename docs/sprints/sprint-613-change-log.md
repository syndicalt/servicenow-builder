# Sprint 613 Change Log

## Stable artifact hash exact-string boundary

Sprint 613 continued production hardening by requiring exact string values before `stable_artifact_hash()` canonicalizes payloads for SHA-256 provenance. The hash path already rejected non-finite numeric values and unsupported non-JSON values, but string subclasses still passed directly through `json.dumps()` and were hashed as ordinary strings.

`_ensure_artifact_hash_payload_json_safe()` now preflights hash payloads before canonical serialization. It accepts exact `str` values and exact `str` mapping keys only. String subclasses fail through the same `artifact hash payload contains non-JSON values` diagnostic as other unsupported values, without echoing payload field names, credential-like keys, object output, or values.

Verification:

- Added 1 failing-first artifact hash test proving a string subclass payload value was accepted and hashed before implementation.
- `python3 -m pytest tests/test_models.py::test_stable_artifact_hash_rejects_string_subclass_values_without_payload_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_models.py -q`: 18 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 687 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2706 tests passed at 93.11% coverage.
