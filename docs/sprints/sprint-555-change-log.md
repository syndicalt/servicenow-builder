# Sprint 555 Change Log

## ServiceNow record-id length guard

Sprint 555 continued production hardening by bounding the shared ServiceNow record-id guard. `_servicenow_record_id()` already rejected non-string, padded, and path-unsafe record ids before URL construction, but it did not cap otherwise valid identifier-shaped values. An oversized identifier made only of allowed characters could therefore reach OAuth acquisition and request construction as an unbounded URL path or query segment.

Record-id validation now rejects values longer than 128 characters before OAuth token acquisition, request construction, or lookup-derived PATCH URL construction. Oversized record ids fail with the fixed `ServiceNow API record id is unsafe` diagnostic. The diagnostic does not echo record id values, URL fragments, query fragments, or credential-like payloads.

This shared guard covers story PATCH ids, generic Table API PATCH ids derived from lookup results, Ready-story project filters, CI/CD Update Set ids, CI/CD progress ids, and attachment target story ids.

Verification:

- Added 1 failing-first ServiceNow record-id length test proving a 129-character record id is rejected before OAuth acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_record_id_before_request -q`: failed before implementation because the oversized record id reached OAuth token acquisition.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_record_id_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_record_id_before_request tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_record_id_before_request tests/test_servicenow.py::test_servicenow_client_updates_story_fields_with_patch_without_secret_leakage tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_cicd_progress_id_before_request tests/test_servicenow.py::test_servicenow_client_previews_commits_and_fetches_cicd_progress -q`: 6 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 157 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 629 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2581 tests passed; required 90% coverage reached with 93.41% total coverage.
