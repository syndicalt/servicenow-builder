# Sprint 522 Change Log

## ServiceNow Table API lookup query delimiter rejection

Sprint 522 continued production hardening by tightening generic ServiceNow Table API lookup query construction. `ServiceNowClient.fetch_table_record()` and `ServiceNowClient.fetch_table_records()` previously interpolated lookup keys and values directly into an encoded `sysparm_query` string with `^` separators. A lookup value containing ServiceNow encoded-query delimiters could change the meaning of the query before the request left the sidecar.

Lookup query construction now rejects lookup keys or values containing `^`, `=`, or control characters before OAuth token acquisition, GET construction, or Table API transport. Unsafe lookup parts fail with the fixed `ServiceNow API lookup query is unsafe` diagnostic. The diagnostic does not echo lookup values, credential-like fragments, or generated query text.

This keeps generic Table API lookup behavior fail-closed for corrupted, hostile, or accidentally malformed lookup inputs: unsupported delimiter material fails before a token is requested and before a query can be sent to ServiceNow with different semantics than the caller intended.

Verification:

- Added 1 failing-first ServiceNow client lookup query test covering a caret-delimited credential-like query injection attempt.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_lookup_query_before_request -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_lookup_query_before_request -q`: 1 test passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 100 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 596 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2491 total tests passed at 93.41% coverage.
