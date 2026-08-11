# Sprint 544 Change Log

## ServiceNow lookup query type guard

Sprint 544 continued production hardening by tightening ServiceNow Table API lookup query construction. `_servicenow_lookup_query()` already rejected lookup keys and values containing encoded-query delimiters, but `_is_unsafe_servicenow_lookup_part()` assumed lookup parts were strings. Hostile non-string lookup keys or values could raise Python `TypeError` diagnostics containing object representations before the fixed ServiceNow validation diagnostic was used.

Lookup query construction now treats non-string lookup keys and values as unsafe before delimiter or control-character checks. Non-string, delimiter-bearing, control-character, or malformed lookup parts fail with the fixed `ServiceNow API lookup query is unsafe` diagnostic before OAuth token acquisition, GET construction, or Table API transport. The diagnostic does not echo object type names, object string output, lookup values, query fragments, or credential-like payloads.

This protects every caller that builds lookup queries through `ServiceNowClient.fetch_table_record()`, `ServiceNowClient.fetch_table_records()`, and the lookup phase of `ServiceNowClient.upsert_table_record()`.

Verification:

- Added 2 failing-first ServiceNow lookup type tests proving hostile lookup keys and values are rejected before OAuth token acquisition or request construction and without calling `str()` or `repr()` for diagnostics.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_lookup_key_before_request tests/test_servicenow.py::test_servicenow_client_rejects_non_string_lookup_value_before_request -q`: failed before implementation because `_is_unsafe_servicenow_lookup_part()` raised `TypeError` with hostile object representations.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_lookup_key_before_request tests/test_servicenow.py::test_servicenow_client_rejects_non_string_lookup_value_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_lookup_query_before_request tests/test_servicenow.py::test_servicenow_client_upserts_table_record_with_lookup_query -q`: 4 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 124 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 618 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2537 tests passed with 93.46% coverage.
