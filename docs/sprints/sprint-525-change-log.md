# Sprint 525 Change Log

## ServiceNow CI/CD path-id rejection

Sprint 525 continued production hardening by tightening ServiceNow CI/CD Update Set URL construction. `ServiceNowClient.preview_cicd_update_set()`, `ServiceNowClient.commit_cicd_update_set()`, and `ServiceNowClient.fetch_cicd_progress()` previously interpolated remote update set ids and progress ids directly into `/api/sn_cicd/.../{id}` URLs. A malformed id containing path or query delimiters could trigger OAuth token acquisition and then change the request path before the sidecar contacted ServiceNow.

CI/CD path ids now reuse the ServiceNow record-id path validator. `remote_update_set_id` and `progress_id` values must be unpadded path segments made of letters, digits, underscores, and hyphens. Unsafe ids fail with the fixed `ServiceNow API record id is unsafe` diagnostic before OAuth token acquisition, URL construction, or CI/CD API transport. The diagnostic does not echo CI/CD ids, URL fragments, credential-like fragments, or generated request paths.

This keeps CI/CD preview, commit, and progress polling behavior fail-closed for corrupted, hostile, or accidentally malformed path ids: unsupported path material fails before a token is requested and before a request can be sent to a ServiceNow route different from the route the caller intended.

Verification:

- Added 1 failing-first ServiceNow CI/CD progress-id test covering a path/query-delimited credential-like progress id.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_cicd_progress_id_before_request -q`: failed before implementation because OAuth token acquisition was attempted before id validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_cicd_progress_id_before_request -q`: 1 test passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 103 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 599 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2497 total tests passed at 93.42% coverage.
