# Sprint 336 Change Log

Scope: Production hardening - local artifact path containment.

## Summary

- Shared local artifact writers now reject unsafe artifact filenames and path components before creating write-once files.
- The covered boundary includes generic JSON artifacts, lifecycle manifests, delivery attachment audits, reviewed delivery manifests, candidate run directories, candidate filenames, writeback audit filenames, and build-claim audit filenames.
- Unsafe artifact names include empty names, `.` or `..`, absolute paths, path separators, and control characters. Operator-controlled run ids, story numbers, build references, and lifecycle event ids cannot escape the configured artifact root through local artifact writers.

## Verification

- `python3 -m pytest tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_path_traversal_filename tests/test_writeback_audit.py::test_lifecycle_manifest_rejects_path_traversal_run_id tests/test_candidates.py::test_candidate_artifact_writer_rejects_path_traversal_run_id -q` - 3 tests failed before implementation because traversal components were accepted.
- `python3 -m pytest tests/test_writeback_audit.py tests/test_candidates.py -q` - 13 passed after implementation.
- `python3 -m pytest tests/test_cli.py tests/test_cli_io.py tests/test_writeback_audit.py tests/test_writeback_audit.py tests/test_runtime_entrypoints.py tests/test_fulfillment_handler.py -q` - 98 passed.
- `python3 -m pytest tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_path_traversal_filename tests/test_writeback_audit.py::test_lifecycle_manifest_rejects_path_traversal_run_id tests/test_candidates.py::test_candidate_artifact_writer_rejects_path_traversal_run_id tests/test_project_docs.py::test_sprint_three_hundred_thirty_six_documents_artifact_path_containment -q` - 4 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 410 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1977 passed, total coverage 93.98%.
