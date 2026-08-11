# Sprint 576 Change Log

## ServiceNow operation URI string-subclass guard

Sprint 576 continued production hardening by preventing discovered ServiceNow Scripted REST operation URI validation from dispatching string methods on hostile string subclasses. `_servicenow_operation_uri()` already rejected non-string, padded, traversal, query-string, fragment, oversized, and malformed operation URI values before import POST construction, but it still accepted `str` subclasses and called `strip()` before returning the fixed `ServiceNow API operation URI is unsafe` diagnostic.

Operation URI validation now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow API operation URI is unsafe` diagnostic before `strip()`, length checks, regex matching, import POST URL construction, or transport calls. This preserves normal discovered Scripted REST operation URI handling while preventing corrupted ServiceNow discovery responses, test transports, or future adapters from surfacing custom exception text, object representations, or credential-like payloads through operation URI string methods.

This keeps `ServiceNowClient.import_update_set_xml()` fail-closed after read-only importer discovery and before constructing the import POST route from unsafe `sys_ws_operation.operation_uri` values.

Verification:

- Added 1 failing-first ServiceNow operation URI string-subclass test proving a hostile `str` subclass raised `RuntimeError` from overridden `strip()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_update_set_importer_operation_uri_str_subclass -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from overridden `strip()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_update_set_importer_operation_uri_str_subclass tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_update_set_importer_operation_uri tests/test_servicenow.py::test_servicenow_client_rejects_oversized_update_set_importer_operation_uri tests/test_servicenow.py::test_servicenow_client_discovers_and_calls_update_set_importer -q`: 4 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 178 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 650 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2623 passed, total coverage 93.39%.
