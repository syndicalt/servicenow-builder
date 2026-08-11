# Sprint 573 Change Log

## ServiceNow table-name string-subclass guard

Sprint 573 continued production hardening by preventing ServiceNow Table API table-name validation from dispatching string methods on hostile string subclasses. `_servicenow_table_name()` already rejected non-string, padded, path-delimiter, oversized, and malformed table names before OAuth token acquisition or request construction, but it still accepted `str` subclasses and called `strip()` before returning the fixed `ServiceNow API table name is unsafe` diagnostic.

Table-name validation now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow API table name is unsafe` diagnostic before `strip()`, length checks, regex matching, OAuth token acquisition, Table API URL construction, or transport calls. This preserves normal table-name handling while preventing internal caller wiring, tests, or future adapters from surfacing custom exception text, object representations, or credential-like payloads through table-name string methods.

This keeps `ServiceNowClient.fetch_table_record()`, `ServiceNowClient.fetch_table_records()`, and `ServiceNowClient.upsert_table_record()` fail-closed before constructing `/api/now/table/{table}` routes from unsafe table-name objects.

Verification:

- Added 1 failing-first ServiceNow table-name string-subclass test proving a hostile `str` subclass raised `RuntimeError` from overridden `strip()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_table_name_str_subclass_without_methods -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from overridden `strip()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_table_name_str_subclass_without_methods tests/test_servicenow.py::test_servicenow_client_rejects_non_string_table_name_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_table_name_before_request tests/test_servicenow.py::test_servicenow_client_rejects_oversized_table_name_before_request tests/test_servicenow.py::test_servicenow_client_fetches_table_record_by_lookup tests/test_servicenow.py::test_servicenow_client_fetches_table_records_by_lookup_and_fields -q`: 6 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 175 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 647 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2617 passed, total coverage 93.38%.
