# Sprint 340 Change Log

Scope: Production hardening - reviewed XML scanner artifact read safety.

## Summary

- Reviewed Update Set XML marker scanning now uses the shared regular-file artifact reader instead of direct `Path.open()`.
- Placeholder detection and `sys_update_xml` marker scanning reject symlinked paths and non-regular filesystem entries before reading XML bytes.
- Reviewed delivery job validation, artifact SHA-256 provenance hashing, and ServiceNow attachment upload now share the same descriptor-safe file boundary.

## Verification

- `python3 -m pytest tests/test_artifact_handoff.py::test_reviewed_delivery_artifact_job_validates_xml_without_path_open -q` - 1 test failed before implementation because XML marker scanning used direct `Path.open()`.
- `python3 -m pytest tests/test_artifact_handoff.py::test_reviewed_delivery_artifact_job_validates_xml_without_path_open tests/test_artifact_handoff.py tests/test_servicenow.py::test_servicenow_client_rejects_symlinked_story_attachment_before_upload tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_without_whole_file_read -q` - 18 passed after implementation.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_forty_documents_xml_scanner_read_safety -q` - 1 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 414 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1987 passed, total coverage 93.96%.
