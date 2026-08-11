# Sprint 744 Change Log - Artifact DTO cause boundary

## Scope

Hardened legacy artifact DTO diagnostics so candidate, writeback audit, and build-claim artifact
serialization failures do not retain unsafe low-level exception instances as public
`ArtifactWriteError` causes.

## Tests First

- Added 3 failing-first artifact DTO cause assertions:
  - `tests/test_candidates.py::test_candidate_artifact_writer_rejects_non_finite_candidate_without_payload_leak`
  - `tests/test_candidates.py::test_candidate_artifact_writer_rejects_non_json_candidate_without_payload_leak`
  - `tests/test_candidates.py::test_candidate_artifact_writer_rejects_string_subclass_candidate_without_payload_leak`
- Initial failures proved the public `ArtifactWriteError` retained unsafe causes for:
  - Candidate `confidence` non-finite numeric rejection.
  - Candidate `SecretBearingObject` unsupported object rejection.
  - Candidate `HostileCandidateText` string subclass rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_744_documents_artifact_dto_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original Pydantic serializer causes in `_artifact_model_json()`.
- Suppressed original non-finite numeric validation causes in `_artifact_model_json()`.
- Suppressed original non-JSON structure validation causes in `_artifact_model_json()`.
- Preserved the existing fixed diagnostics:
  - `artifact DTO payload contains non-finite numeric values`
  - `artifact DTO payload contains non-JSON values`
- Documented the artifact DTO cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_candidates.py -q -k "candidate_artifact_writer_rejects"` failed first
  with 3 failures and 2 passing selected tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_744` failed first with 1 failure.
- `python3 -m pytest tests/test_candidates.py -q -k "candidate_artifact_writer_rejects"` passed with
  5 tests and 4 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_744` passed with 1 test and 817
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_candidates.py -q` passed with 9 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3074 tests and 93.33% total coverage.
