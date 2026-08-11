# Sprint 584 Change Log

## ServiceNow lookup response text string-subclass guard

Sprint 584 continued production hardening by preventing ServiceNow upsert lookup response normalization from accepting string subclasses as primitive lookup text. `_servicenow_lookup_text()` already rejected unsupported objects, bytes, containers, floats, and non-scalar values from existing-record lookup responses before `ServiceNowClient.upsert_table_record()` built a PATCH URL, but it still accepted `str` subclasses and let the later record-id guard reject them with `ServiceNow API record id is unsafe`.

Lookup response text normalization now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow API lookup contains non-JSON value` diagnostic before record-id validation, PATCH URL construction, create/update decision reporting, or Table API transport. This keeps the failure at the ServiceNow response normalization boundary and preserves the distinction between malformed upstream lookup data and caller-supplied record-id path validation.

This keeps `ServiceNowClient.upsert_table_record()` fail-closed before constructing PATCH URLs from unsafe existing-record `sys_id` response values.

Verification:

- Added 1 failing-first ServiceNow lookup response text string-subclass test proving a subclassed existing-record `sys_id` returned `ServiceNow API record id is unsafe` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_upsert_rejects_existing_record_sys_id_str_subclass -q`: failed before implementation because the subclassed lookup response text reached record-id validation instead of failing with `ServiceNow API lookup contains non-JSON value`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_upsert_rejects_existing_record_sys_id_str_subclass tests/test_servicenow.py::test_servicenow_client_upsert_rejects_non_json_existing_record_sys_id tests/test_servicenow.py::test_servicenow_client_upserts_table_record_with_lookup_query -q`: 3 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_584_documents_servicenow_lookup_response_text_str_subclass_guard -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 187 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 658 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2640 passed, 93.39% coverage.
