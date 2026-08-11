# Sprint 341 Change Log

Scope: Production hardening - delivery smoke XML exclusive artifact creation.

## Summary

- Delivery smoke XML export creation now uses the shared exclusive-create text artifact writer instead of an exists-then-`write_text()` sequence.
- `run-delivery-artifact-smoke` and `run-reviewed-delivery-smoke` reject existing files, existing symlinks, and broken symlinks before writing XML content.
- This prevents smoke export overwrites and broken-symlink redirection outside the configured artifact root while preserving normal smoke handoff behavior.

## Verification

- `python3 -m pytest tests/test_cli.py::test_cli_run_reviewed_delivery_smoke_rejects_broken_symlink_export -q` - 1 test failed before implementation because reviewed smoke XML creation could reach a symlinked export path before CLI rejection.
- `python3 -m pytest tests/test_cli.py::test_cli_run_delivery_artifact_smoke_rejects_broken_symlink_export tests/test_cli.py::test_cli_run_reviewed_delivery_smoke_rejects_broken_symlink_export tests/test_cli.py::test_cli_run_delivery_artifact_smoke_creates_placeholder_and_plans_attachment tests/test_cli.py::test_cli_run_reviewed_delivery_smoke_creates_reviewed_handoff_path tests/test_writeback_audit.py::test_write_json_artifact_once_rejects_broken_symlink_escape tests/test_candidates.py::test_candidate_artifact_writer_rejects_broken_symlink_escape -q` - 6 passed after implementation.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_forty_one_documents_smoke_xml_exclusive_create tests/test_cli.py::test_cli_run_delivery_artifact_smoke_rejects_broken_symlink_export tests/test_cli.py::test_cli_run_reviewed_delivery_smoke_rejects_broken_symlink_export -q` - 3 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 415 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1990 passed, total coverage 93.99%.
