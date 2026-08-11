# Sprint 490 Change Log

## Stable artifact hash non-JSON value rejection

Hardened shared artifact provenance hashing so `stable_artifact_hash()` cannot mint SHA-256 values from unsupported Python payload values coerced through `str()`.

Sprint 465 rejected non-finite numeric values in artifact hash payloads. This sprint closes the adjacent structural JSON gap: unsupported objects, bytes, and other non-JSON values now fail before canonicalization and hash computation. The fixed diagnostic is `artifact hash payload contains non-JSON values`, and it does not echo malformed field names, object type names, object string output, credential-like keys, or values.

## Verification

- Added 1 failing-first artifact hash test proving an object with secret-bearing `__str__` output was previously accepted and hashed.
- `python3 -m pytest tests/test_models.py::test_stable_artifact_hash_rejects_non_json_values_without_payload_leak -q`: failed before implementation because no exception was raised.
- `python3 -m pytest tests/test_models.py::test_stable_artifact_hash_rejects_non_json_values_without_payload_leak tests/test_models.py::test_stable_artifact_hash_rejects_non_finite_values_without_payload_leak tests/test_models.py::test_stable_artifact_hash_is_order_independent_for_mapping_keys -q`: 3 tests passed.
- `python3 -m pytest tests/test_models.py -q`: 17 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 564 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2423 total tests passed at 93.82% coverage.
