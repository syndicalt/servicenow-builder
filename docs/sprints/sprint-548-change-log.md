# Sprint 548 Change Log

## ServiceNow story response text type guard

Sprint 548 continued production hardening by tightening ServiceNow story response ingestion. `_story_from_record()` previously converted required story text, optional acceptance criteria, and AI writeback context fields with `str()`. A hostile or corrupted alternate transport response could therefore place object string output into `Story` values, downstream artifacts, work notes, or diagnostics before a fixed ServiceNow response diagnostic was used.

Story response parsing now accepts only string values for required story text fields, optional acceptance criteria, and AI additional-context fields. Non-string response text fails with the fixed `ServiceNow API story response field is unsafe` diagnostic before a `Story` is constructed. The diagnostic does not echo object type names, object string output, story values, additional-context values, or credential-like payloads.

This protects `ServiceNowClient.fetch_stories()` and `ServiceNowClient.fetch_ready_stories()` before story records leave the ServiceNow client boundary.

Verification:

- Added 1 failing-first ServiceNow story response text test proving a hostile non-string story number from a transport response is rejected without stringifying object output into a `Story`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_response_text_without_stringifying -q`: failed before implementation because `_story_from_record()` accepted the hostile object by calling `str()`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_requests_and_maps_writeback_idempotency_fields tests/test_servicenow.py::test_servicenow_client_maps_missing_optional_record_values_to_safe_defaults -q`: 3 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 129 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 622 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2546 tests passed with 93.46% coverage.
