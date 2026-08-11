# Sprint 494 Change Log

## Legacy artifact DTO non-JSON value rejection

Hardened `_artifact_model_json()` so legacy Pydantic DTO artifact writers cannot fail through raw Pydantic serializer diagnostics when a corrupted in-process DTO contains unsupported Python values.

Sprint 476 rejected non-finite numeric DTO values. This sprint closes the adjacent structural JSON gap: unsupported objects, bytes, and other non-JSON values now fail before write-once candidate, writeback audit, or build-claim audit artifact output with the fixed `artifact DTO payload contains non-JSON values` diagnostic. The diagnostic does not echo DTO field names, object type names, object string output, story identifiers, audit values, credential-like keys, or payload values.

The implementation preserves valid Pydantic-native DTO values by preflighting Python-mode payloads, then using Pydantic JSON-mode output for artifact rendering.

## Verification

- Added 1 failing-first candidate artifact writer test proving an object with secret-bearing `__str__` output previously surfaced a raw Pydantic serializer diagnostic.
- `python3 -m pytest tests/test_candidates.py::test_candidate_artifact_writer_rejects_non_json_candidate_without_payload_leak -q`: failed before implementation because the diagnostic reflected the local object type name.
- `python3 -m pytest tests/test_candidates.py::test_candidate_artifact_writer_rejects_non_json_candidate_without_payload_leak tests/test_candidates.py::test_candidate_artifact_writer_rejects_non_finite_candidate_without_payload_leak tests/test_candidates.py::test_candidate_artifact_writer_refuses_to_overwrite_existing_run_file -q`: 3 tests passed.
- `python3 -m pytest tests/test_candidates.py -q`: 8 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 568 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2431 total tests passed at 93.75% coverage.
