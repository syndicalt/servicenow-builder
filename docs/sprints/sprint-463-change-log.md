# Sprint 463 Change Log

## Artifact JSON output non-finite number rejection

Hardened shared write-once JSON artifact serialization so durable audit artifacts cannot be written
with non-standard JSON numeric constants such as `NaN`, `Infinity`, or `-Infinity`. Python
`json.dumps()` emits those constants by default, which meant a malformed local report payload,
handoff payload, or future worker artifact payload could produce non-strict JSON evidence even after
the input and provider boundaries rejected the same values.

`write_json_artifact_once()` now serializes with strict JSON numeric handling and raises
`ArtifactWriteError` with the fixed `artifact JSON payload contains non-finite numeric values`
diagnostic before opening the target file. The diagnostic does not echo payload field names,
credential-like keys, or values, and the existing write-once, symlink, and path traversal controls
remain unchanged.

## Verification

- Added 1 failing-first artifact serialization test covering non-finite payload rejection before
  file creation and without payload-field or credential-value reflection.
- `python3 -m pytest tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_non_finite_payload_without_file_or_leak -q`:
  failed before implementation because `NaN` was written into the artifact file.
- `python3 -m pytest tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_existing_file tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_non_finite_payload_without_file_or_leak tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_broken_symlink_escape tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_path_traversal_filename -q`:
  4 tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 537 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2367 total tests passed at 93.83% coverage.
