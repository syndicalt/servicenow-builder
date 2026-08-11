# Sprint 542 Change Log

## ServiceNow record-id type guard

Sprint 542 continued production hardening by tightening the shared ServiceNow record-id validator. `_servicenow_record_id()` previously assumed record ids were strings and called `.strip()` before type checking, so hostile non-string record-id values could raise Python `AttributeError` diagnostics containing object representations before the fixed ServiceNow validation diagnostic was used.

The shared record-id validator now rejects non-string values before any string operations or regex matching. Non-string, padded, delimiter-bearing, control-character, or malformed record ids fail with the fixed `ServiceNow API record id is unsafe` diagnostic. The diagnostic does not echo object type names, object string output, record id values, URL fragments, query fragments, or credential-like payloads.

This protects every caller that uses the shared record-id guard, including story PATCH path ids, generic upsert PATCH ids, ready-story project filters, attachment story ids, CI/CD retrieve ids, CI/CD path ids, and progress ids.

Verification:

- Added 1 failing-first ServiceNow non-string record-id test proving hostile story PATCH path ids are rejected before OAuth token acquisition or request construction and without calling `str()` or `repr()` for diagnostics.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_record_id_before_request -q`: failed before implementation because `_servicenow_record_id()` raised `AttributeError` with the hostile object representation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_record_id_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_record_id_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_cicd_progress_id_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_story_id_before_read tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_ready_story_project_id_before_request -q`: 5 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 121 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 616 tests passed after documentation updates.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues across 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2532 tests passed with 93.45% coverage.
