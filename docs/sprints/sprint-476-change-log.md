# Sprint 476 Change Log

## Legacy DTO artifact writer non-finite number rejection

Hardened legacy Pydantic DTO artifact writers so candidate artifacts, writeback audit artifacts, and build-claim audit artifacts cannot silently normalize corrupted in-process DTOs containing `NaN`, `Infinity`, or `-Infinity`.
These helper paths predate the shared strict JSON artifact writer and used direct `model_dump_json()`
output.

`_artifact_model_json()` now preflights Python-mode Pydantic DTO payloads with strict JSON numeric
handling before returning the established pretty JSON artifact body. Non-finite DTO artifact
payloads fail with `artifact DTO payload contains non-finite numeric values`. The diagnostic is
stable and does not echo DTO field names, story identifiers, audit values, or payload values.

## Verification

- Added 1 failing-first candidate artifact writer test covering a non-finite candidate confidence
  value without field-name, story-number, or value reflection.
- `python3 -m pytest tests/test_candidates.py::test_candidate_artifact_writer_rejects_non_finite_candidate_without_payload_leak -q`:
  failed before implementation because the candidate artifact writer did not reject non-finite DTO
  payloads.
- `python3 -m pytest tests/test_candidates.py::test_candidate_artifact_writer_rejects_non_finite_candidate_without_payload_leak tests/test_candidates.py::test_candidate_artifact_writer_refuses_to_overwrite_existing_run_file tests/test_candidates.py::test_candidate_artifact_writer_rejects_broken_symlink_escape tests/test_candidates.py::test_candidate_artifact_writer_rejects_path_traversal_run_id -q`:
  4 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 550 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2395 total tests passed at 93.86% coverage.
