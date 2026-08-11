# Sprint 524 Change Log

## ServiceNow Table API record-id path rejection

Sprint 524 continued production hardening by tightening ServiceNow Table API record URL construction. `ServiceNowClient.update_story_fields()` and the PATCH branch of `ServiceNowClient.upsert_table_record()` previously interpolated record ids directly into `/api/now/table/{table}/{sys_id}` URLs. A malformed record id containing path or query delimiters could change the request path before the sidecar contacted ServiceNow.

Table API record ids used in URL paths now must be unpadded path segments made of letters, digits, underscores, and hyphens. Unsafe record ids fail with the fixed `ServiceNow API record id is unsafe` diagnostic before OAuth token acquisition, URL construction, or Table API transport. The diagnostic does not echo record id values, URL fragments, credential-like fragments, or generated request paths.

This keeps direct story updates and generic Table API update behavior fail-closed for corrupted, hostile, or accidentally malformed record ids: unsupported path material fails before a token is requested and before a request can be sent to a ServiceNow route different from the route the caller intended.

Verification:

- Added 1 failing-first ServiceNow client record-id test covering a path/query-delimited credential-like story sys_id value.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_record_id_before_request -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_record_id_before_request -q`: 1 test passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 102 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 598 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2495 total tests passed at 93.42% coverage.
