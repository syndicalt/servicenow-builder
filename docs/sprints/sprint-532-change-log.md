# Sprint 532 Change Log

## ServiceNow sysparm_limit range guard

Sprint 532 continued production hardening by bounding ServiceNow Table API result limits. `ServiceNowClient.fetch_stories()` and `ServiceNowClient.fetch_table_records()` previously converted caller-provided integer limits directly into `sysparm_limit`. That left non-positive and oversized values to reach OAuth acquisition or the ServiceNow request path.

ServiceNow result limits are now validated before request construction. The accepted range is 1 through 500, matching the largest current discovery and context-gathering fetches in the codebase. Boolean, non-positive, and oversized values fail with the fixed `ServiceNow API result limit is unsafe` diagnostic before OAuth token acquisition, GET construction, or Table API transport. The diagnostic does not echo query values, lookup values, or credential-like payloads.

This keeps the client from accidentally issuing unbounded or malformed ServiceNow reads while preserving existing legitimate discovery limits.

Verification:

- Added 2 failing-first ServiceNow result-limit tests proving non-positive story limits and oversized table-record limits are rejected before OAuth token acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_positive_story_limit_before_request tests/test_servicenow.py::test_servicenow_client_rejects_oversized_table_record_limit_before_request -q`: failed before implementation because the fixed result-limit diagnostic did not exist.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_positive_story_limit_before_request tests/test_servicenow.py::test_servicenow_client_rejects_oversized_table_record_limit_before_request tests/test_servicenow.py::test_servicenow_client_fetch_stories_allows_explicit_query tests/test_servicenow.py::test_servicenow_client_fetches_table_records_by_lookup_and_fields -q`: 4 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 111 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 606 documentation tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2512 tests passed with 93.44% coverage.
