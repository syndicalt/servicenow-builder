# Sprint 558 Change Log

## ServiceNow operation URI length guard

Sprint 558 continued production hardening by bounding the discovered Scripted REST operation URI used by `ServiceNowClient.import_update_set_xml()`. `_servicenow_operation_uri()` already rejected non-string, padded, traversal, query-string, fragment, and regex-unsafe operation URI values from `sys_ws_operation.operation_uri`, but it did not cap otherwise valid `/api/<namespace>/<service>` values before using them to build the import POST URL.

Operation URI validation now rejects values longer than 256 characters after read-only importer discovery and before the XML import POST is constructed. Oversized operation URIs fail with the fixed `ServiceNow API operation URI is unsafe` diagnostic. The diagnostic does not echo operation URI values, URL fragments, query strings, ServiceNow response internals, or credential-like payloads.

This keeps Update Set importer handoff fail-closed for corrupted or hostile ServiceNow discovery responses that provide syntactically valid but unbounded operation URI material.

Verification:

- Added 1 failing-first ServiceNow importer operation URI length test proving a regex-valid oversized URI reached the import POST path before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_update_set_importer_operation_uri -q`: failed before implementation because the oversized operation URI did not raise `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_update_set_importer_operation_uri tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_update_set_importer_operation_uri tests/test_servicenow.py::test_servicenow_client_discovers_and_calls_update_set_importer -q`: 3 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 160 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 632 passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2587 passed, 93.41% total coverage.
