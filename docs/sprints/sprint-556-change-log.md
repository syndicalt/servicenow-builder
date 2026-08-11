# Sprint 556 Change Log

## ServiceNow table-name length guard

Sprint 556 continued production hardening by bounding the shared ServiceNow table-name guard. `_servicenow_table_name()` already rejected non-string, padded, and path-unsafe table names before URL construction, but it did not cap otherwise valid identifier-shaped values. An oversized table name made only of allowed characters could therefore reach OAuth acquisition and request construction as an unbounded Table API path segment.

Table-name validation now rejects values longer than 128 characters before OAuth token acquisition or request construction. Oversized table names fail with the fixed `ServiceNow API table name is unsafe` diagnostic. The diagnostic does not echo table values, URL fragments, or credential-like payloads.

This shared guard covers generic Table API fetch, list, and upsert paths before `/api/now/table/{table}` URLs can be constructed.

Verification:

- Added 1 failing-first ServiceNow table-name length test proving a 129-character table name is rejected before OAuth acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_table_name_before_request -q`: failed before implementation because the oversized table name reached OAuth token acquisition.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_table_name_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_table_name_before_request tests/test_servicenow.py::test_servicenow_client_rejects_non_string_table_name_before_request tests/test_servicenow.py::test_servicenow_client_fetches_table_record_by_lookup tests/test_servicenow.py::test_servicenow_client_fetches_table_records_by_lookup_and_fields tests/test_servicenow.py::test_servicenow_client_upserts_table_record_with_lookup_query -q`: 6 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 158 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 630 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2583 tests passed; required 90% coverage reached with 93.41% total coverage.
