# Sprint 523 Change Log

## ServiceNow Table API table-name path rejection

Sprint 523 continued production hardening by tightening generic ServiceNow Table API URL construction. `ServiceNowClient.upsert_table_record()`, `ServiceNowClient.fetch_table_record()`, and `ServiceNowClient.fetch_table_records()` previously interpolated caller-provided table names directly into `/api/now/table/{table}` URLs. A malformed table value containing path or query delimiters could change the request path before the sidecar contacted ServiceNow.

Generic Table API table names now must be unpadded identifiers made of letters, digits, and underscores, starting with a letter. Unsafe table names fail with the fixed `ServiceNow API table name is unsafe` diagnostic before OAuth token acquisition, URL construction, or Table API transport. The diagnostic does not echo table values, URL fragments, credential-like fragments, or generated request paths.

This keeps generic Table API behavior fail-closed for corrupted, hostile, or accidentally malformed table names: unsupported path material fails before a token is requested and before a request can be sent to a ServiceNow route different from the route the caller intended.

Verification:

- Added 1 failing-first ServiceNow client table-name test covering a path/query-delimited credential-like table value.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_table_name_before_request -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_table_name_before_request -q`: 1 test passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 101 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 597 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2493 total tests passed at 93.42% coverage.
