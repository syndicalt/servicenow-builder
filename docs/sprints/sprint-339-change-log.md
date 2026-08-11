# Sprint 339 Change Log

Scope: Production hardening - ServiceNow attachment artifact read safety.

## Summary

- ServiceNow story attachment uploads now use the shared regular-file artifact reader instead of `Path.read_bytes()`.
- Attachment upload rejects symlinked paths and non-regular filesystem entries before OAuth token acquisition or Attachment API upload.
- Attachment content is read in bounded chunks with the existing 10 MiB maximum preserved.
- The same descriptor-safe artifact read boundary now covers provenance hashing and ServiceNow attachment handoff.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_symlinked_story_attachment_before_upload tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_without_whole_file_read -q` - 2 tests failed before implementation because symlinked uploads reached transport and normal upload used `Path.read_bytes()`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_symlinked_story_attachment_before_upload tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_without_whole_file_read tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_attachment_before_reading tests/test_writeback_audit.py::test_artifact_sha256_file_rejects_symlinked_artifact -q` - 4 passed after implementation.
- `python3 -m pytest tests/test_servicenow.py tests/test_cli.py::test_cli_attach_delivery_artifacts_dry_run_does_not_attach tests/test_cli.py::test_cli_attach_delivery_artifacts_hash_check_uses_streaming_read tests/test_cli.py::test_cli_attach_delivery_artifacts_dry_run_blocks_missing_artifact tests/test_cli.py::test_cli_attach_delivery_artifacts_blocks_hash_mismatch_before_attachment tests/test_writeback_audit.py tests/test_artifact_handoff.py -q` - 104 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_thirty_nine_documents_attachment_read_safety -q` - 1 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 413 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1985 passed, total coverage 93.96%.
