# Sprint 543 Change Log

## ServiceNow table-name type guard

Sprint 543 continued production hardening by tightening the shared ServiceNow table-name validator. `_servicenow_table_name()` previously assumed table names were strings and called `.strip()` before type checking, so hostile non-string table-name values could raise Python `AttributeError` diagnostics containing object representations before the fixed ServiceNow validation diagnostic was used.

The shared table-name validator now rejects non-string values before any string operations or regex matching. Non-string, padded, delimiter-bearing, control-character, or malformed table names fail with the fixed `ServiceNow API table name is unsafe` diagnostic. The diagnostic does not echo object type names, object string output, table values, URL fragments, or credential-like payloads.

This protects every caller that uses the shared table-name guard, including `ServiceNowClient.upsert_table_record()`, `ServiceNowClient.fetch_table_record()`, and `ServiceNowClient.fetch_table_records()`.

Verification:

- Added 1 failing-first ServiceNow non-string table-name test proving hostile generic Table API table names are rejected before OAuth token acquisition or request construction and without calling `str()` or `repr()` for diagnostics.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_table_name_before_request -q`: failed before implementation because `_servicenow_table_name()` raised `AttributeError` with the hostile object representation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_table_name_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_table_name_before_request tests/test_servicenow.py::test_servicenow_client_upserts_table_record_with_lookup_query tests/test_servicenow.py::test_servicenow_client_fetches_table_records_by_lookup_and_fields -q`: 4 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 122 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 617 tests passed after documentation updates.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues across 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2534 tests passed with 93.45% coverage.
