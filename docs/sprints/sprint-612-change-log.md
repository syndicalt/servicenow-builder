# Sprint 612 Change Log

## Artifact DTO exact-string output boundary

Sprint 612 continued production hardening by requiring exact string values before legacy Pydantic DTO artifact writers emit write-once JSON artifacts. `_artifact_model_json()` already rejected non-finite numeric values and unsupported non-JSON values, but string subclasses still passed the DTO payload preflight and could be serialized as ordinary strings.

`_ensure_artifact_dto_payload_json_safe()` now accepts exact `str` values and exact `str` mapping keys only. String subclasses fail through the same `artifact DTO payload contains non-JSON values` diagnostic as other unsupported values, without echoing DTO field names, story identifiers, audit values, object output, or payload values.

Verification:

- Added 1 failing-first candidate artifact test proving a string subclass DTO value was accepted and written before implementation.
- `python3 -m pytest tests/test_candidates.py::test_candidate_artifact_writer_rejects_string_subclass_candidate_without_payload_leak -q`: failed before implementation because no `ArtifactWriteError` was raised.
- `python3 -m pytest tests/test_candidates.py -q`: 9 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 686 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2704 tests passed at 93.13% coverage.
