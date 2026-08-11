# Sprint 745 Change Log - Artifact JSON output cause boundary

## Scope

Hardened generic write-once JSON artifact diagnostics so non-finite payload serialization failures
do not retain unsafe low-level JSON encoder exceptions as public `ArtifactWriteError` causes.

## Tests First

- Added 1 failing-first artifact JSON output cause assertion:
  - `tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_non_finite_payload_without_file_or_leak`
- Initial failure proved the public `ArtifactWriteError` retained the JSON encoder cause for:
  - Generic artifact payload `bad_score` non-finite numeric rejection with `artifact-secret` in the
    same payload.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_745_documents_artifact_json_output_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original JSON encoder causes in `write_json_artifact_once()` for non-finite payload
  failures.
- Preserved the existing fixed diagnostic:
  - `artifact JSON payload contains non-finite numeric values`
- Documented the artifact JSON output cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_writeback_audit.py -q -k "write_json_artifact_once_rejects_non_finite"`
  failed first with 1 failure.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_745` failed first with 1 failure.
- `python3 -m pytest tests/test_writeback_audit.py -q -k "write_json_artifact_once_rejects_non_finite"`
  passed with 1 test and 13 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_745` passed with 1 test and 818
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_writeback_audit.py -q` passed with 14 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3075 tests and 93.33% total coverage.
