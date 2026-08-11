# Sprint 530 Change Log

## ServiceNow ready-story project-id query injection guard

Sprint 530 continued production hardening by tightening `ServiceNowClient.fetch_ready_stories(project_sys_id=...)`. The method builds the encoded query `state=Ready^project=<id>`, but previously interpolated the provided project id directly. A malformed project id containing ServiceNow encoded-query delimiters such as `^` or `=` could alter the query before the request was sent.

Ready-story project filters now validate `project_sys_id` with the same ServiceNow record-id safety rule used for URL path ids before constructing the encoded query. Unsafe project ids fail with the fixed `ServiceNow API record id is unsafe` diagnostic before OAuth token acquisition, GET construction, or Table API transport. The diagnostic does not echo project id values, encoded-query fragments, or credential-like payloads.

This preserves explicit-query behavior for `fetch_stories(sysparm_query=...)` while making the typed project-filter convenience path fail closed.

Verification:

- Added 1 failing-first ServiceNow ready-story project-id test proving unsafe encoded-query delimiters are rejected before OAuth token acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_ready_story_project_id_before_request -q`: failed before implementation because OAuth token acquisition was attempted before project id validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_ready_story_project_id_before_request tests/test_servicenow.py::test_servicenow_client_builds_read_only_story_query_without_credentials -q`: 2 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 108 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 604 documentation tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2507 tests passed with 93.43% coverage.
