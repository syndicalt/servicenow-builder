# Sprint 337 Change Log

Scope: Production hardening - exclusive local artifact creation.

## Summary

- Local artifact writers now create artifacts with exclusive file creation instead of an exists-then-write sequence.
- The shared write path rejects existing files, existing symlinks, and broken symlinks before any content is written.
- Generic JSON artifacts, lifecycle manifests, delivery attachment audits, reviewed delivery manifests, candidate artifacts, writeback audit artifacts, and build-claim audit artifacts inherit the same write-once behavior.
- This closes artifact overwrite races and prevents broken symlink redirection from writing audit content outside the configured artifact root.

## Verification

- `python3 -m pytest tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_broken_symlink_escape tests/test_candidates.py::test_candidate_artifact_writer_rejects_broken_symlink_escape -q` - 2 tests failed before implementation because broken symlinks redirected writes outside the artifact root.
- `python3 -m pytest tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_broken_symlink_escape tests/test_candidates.py::test_candidate_artifact_writer_rejects_broken_symlink_escape tests/test_writeback_audit.py tests/test_candidates.py -q` - 15 passed after implementation.
- `python3 -m pytest tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_broken_symlink_escape tests/test_candidates.py::test_candidate_artifact_writer_rejects_broken_symlink_escape tests/test_project_docs.py::test_sprint_three_hundred_thirty_seven_documents_exclusive_artifact_create -q` - 3 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 411 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1980 passed, total coverage 93.99%.
