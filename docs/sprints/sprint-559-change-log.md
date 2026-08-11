# Sprint 559 Change Log

## ServiceNow lookup part length guard

Sprint 559 continued production hardening by bounding ServiceNow encoded-query lookup parts. `_servicenow_lookup_query()` already rejected non-string lookup keys and values, encoded-query delimiters, and control characters before constructing `sysparm_query`, but otherwise safe-looking lookup values could be arbitrarily large and still reach OAuth acquisition and request construction.

Lookup part validation now rejects keys or values longer than 1024 characters before OAuth token acquisition, encoded-query assembly, GET construction, lookup-derived PATCH decisions, or Table API transport. Oversized lookup parts fail with the fixed `ServiceNow API lookup query is unsafe` diagnostic. The diagnostic does not echo lookup values, query fragments, object representations, or credential-like payloads.

This shared guard covers `ServiceNowClient.fetch_table_record()`, `ServiceNowClient.fetch_table_records()`, and lookup branches used by `ServiceNowClient.upsert_table_record()`.

Verification:

- Added 1 failing-first ServiceNow lookup part length test proving a 1025-character lookup value reached OAuth token acquisition before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_lookup_value_before_request -q`: failed before implementation because the oversized lookup value reached OAuth token acquisition.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_lookup_value_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_lookup_query_before_request tests/test_servicenow.py::test_servicenow_client_rejects_non_string_lookup_key_before_request tests/test_servicenow.py::test_servicenow_client_rejects_non_string_lookup_value_before_request tests/test_servicenow.py::test_servicenow_client_fetches_table_record_by_lookup tests/test_servicenow.py::test_servicenow_client_fetches_table_records_by_lookup_and_fields tests/test_servicenow.py::test_servicenow_client_upserts_table_record_with_lookup_query -q`: 7 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 161 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 633 passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2589 passed, 93.41% total coverage.
