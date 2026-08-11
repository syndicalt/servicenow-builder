# Sprint 757 Change Log - Artifact filesystem cause boundary

## Scope

Hardened local artifact filesystem diagnostics so write-once collisions and symlink or non-regular read failures do not retain unsafe lower-level filesystem exceptions as public artifact error causes.

## Tests First

- Added 2 failing-first artifact filesystem cause assertions:
  - `tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_existing_file`
  - `tests/test_writeback_audit.py::test_artifact_sha256_file_rejects_symlinked_artifact`
- Initial failures proved `ArtifactWriteError` retained `FileExistsError` for existing artifacts and `ArtifactReadError` retained `OSError` for symlinked artifact reads.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_757_documents_artifact_filesystem_cause_boundary`
- The documentation assertion was added before the sprint log and operator guide update, so the docs gate covers the new operator-facing contract.

## Changes

- Suppressed original `FileExistsError` causes in `write_text_artifact_once()`.
- Suppressed original symlink `OSError` causes in `open_artifact_for_read()`.
- Preserved fixed diagnostics:
  - `artifact already exists: <path>`
  - `artifact path must be a regular file: <path>`
- Documented the artifact filesystem cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_writeback_audit.py -q -k "rejects_existing_file or rejects_symlinked_artifact"` - 2 passed, 12 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_757` - 1 passed, 830 deselected.
- `python3 -m pytest tests/test_writeback_audit.py -q` - 14 passed.
- `ruff check src tests` - passed.
- `mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3095 passed, 93.38% coverage.
