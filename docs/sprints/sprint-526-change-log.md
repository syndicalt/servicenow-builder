# Sprint 526 Change Log

## ServiceNow importer operation URI path rejection

Sprint 526 continued production hardening by tightening the discovered Scripted REST operation URI used by `ServiceNowClient.import_update_set_xml()`. The client discovers `sys_ws_operation.operation_uri` for the reviewed Update Set importer endpoint, then appends that URI to the configured ServiceNow instance URL. The previous check only required the value to start with `/api/`, which still allowed traversal, query strings, fragments, and other ambiguous path material.

Importer operation URI handling now accepts only string values shaped like `/api/<namespace>/<service>`, where namespace and service contain letters, digits, and underscores. Unsupported objects, bytes, containers, traversal markers, query strings, fragments, controls, padded values, and non-matching paths fail with the fixed `ServiceNow API operation URI is unsafe` diagnostic. The diagnostic does not echo operation URI values, URL fragments, query strings, credential-like fragments, or ServiceNow response internals.

This keeps Update Set importer handoff fail-closed for corrupted or hostile ServiceNow discovery responses: unsafe operation URI material fails after read-only discovery and before an import POST can be constructed or sent to a different route than intended.

Verification:

- Added 1 failing-first ServiceNow importer operation URI test covering a traversal/query-delimited credential-like operation URI.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_update_set_importer_operation_uri -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_update_set_importer_operation_uri -q`: 1 test passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 104 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 600 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2499 total tests passed at 93.43% coverage.
