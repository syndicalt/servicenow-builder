# Sprint 582 Change Log

## ServiceNow lookup part string-subclass guard

Sprint 582 continued production hardening by preventing ServiceNow encoded-query lookup part validation from dispatching string behavior on hostile string subclasses. `_is_unsafe_servicenow_lookup_part()` already rejected non-string, delimiter-bearing, control-character, and oversized lookup keys and values before `_servicenow_lookup_query()` assembled `sysparm_query`, but it still accepted `str` subclasses and iterated them during control-character checks before returning the fixed `ServiceNow API lookup query is unsafe` diagnostic.

Lookup part validation now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow API lookup query is unsafe` diagnostic before delimiter checks, length checks, control-character scans, encoded-query assembly, OAuth token acquisition, GET construction, upsert lookup decisions, or Table API transport. This preserves normal lookup query construction while preventing internal caller wiring, tests, or future adapters from surfacing custom exception text, object representations, or credential-like payloads through lookup-part string behavior.

This keeps `ServiceNowClient.fetch_table_record()`, `ServiceNowClient.fetch_table_records()`, and lookup-backed `ServiceNowClient.upsert_table_record()` fail-closed before constructing ServiceNow encoded queries from unsafe lookup keys or values.

Verification:

- Added 2 failing-first ServiceNow lookup part string-subclass tests proving hostile lookup key and value `str` subclasses raised `RuntimeError` from overridden `__iter__()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_lookup_key_str_subclass_before_request tests/test_servicenow.py::test_servicenow_client_rejects_lookup_value_str_subclass_before_request -q`: failed before implementation because the hostile string subclasses raised `RuntimeError` from overridden `__iter__()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_lookup_key_str_subclass_before_request tests/test_servicenow.py::test_servicenow_client_rejects_lookup_value_str_subclass_before_request tests/test_servicenow.py::test_servicenow_client_rejects_non_string_lookup_key_before_request tests/test_servicenow.py::test_servicenow_client_rejects_non_string_lookup_value_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_lookup_query_before_request tests/test_servicenow.py::test_servicenow_client_rejects_oversized_lookup_value_before_request tests/test_servicenow.py::test_servicenow_client_upserts_table_record_with_lookup_query -q`: 7 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_544_documents_servicenow_lookup_query_type_guard tests/test_project_docs.py::test_sprint_582_documents_servicenow_lookup_part_str_subclass_guard -q`: 2 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 185 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 656 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2636 passed, 93.39% coverage.
