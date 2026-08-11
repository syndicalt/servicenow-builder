# Sprint 338 Change Log

Scope: Production hardening - artifact provenance read safety.

## Summary

- Local artifact SHA-256 provenance hashing now validates the filesystem entry before streaming file contents.
- Symlinked artifact paths and non-regular filesystem entries are rejected with `ArtifactReadError` instead of being followed or hashed.
- Missing artifact paths continue to use the existing fail-closed missing-file behavior.
- Lifecycle manifests, handoff reports, reviewed delivery jobs, and attachment verification now share the same regular-file evidence boundary.

## Verification

- `python3 -m pytest tests/test_writeback_audit.py::test_artifact_sha256_file_rejects_symlinked_artifact -q` - 1 test failed before implementation because the read-side artifact error type and symlink rejection boundary did not exist.
- `python3 -m pytest tests/test_writeback_audit.py::test_artifact_sha256_file_rejects_symlinked_artifact tests/test_writeback_audit.py tests/test_artifact_handoff.py tests/test_cli.py::test_cli_attach_delivery_artifacts_dry_run_blocks_missing_artifact -q` - 26 passed after implementation.
- `python3 -m pytest tests/test_writeback_audit.py::test_artifact_sha256_file_rejects_symlinked_artifact tests/test_project_docs.py::test_sprint_three_hundred_thirty_eight_documents_artifact_read_safety -q` - 2 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 412 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1982 passed, total coverage 93.99%.
