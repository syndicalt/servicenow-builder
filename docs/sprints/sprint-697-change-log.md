# Sprint 697 Change Log - ServiceNow Table API response status boundary

## Scope

Centralized ServiceNow Table API response status handling so regular client methods validate the
transport response object and status code before success/failure branching, error formatting, or
result parsing.

## Tests First

- Added 4 failing-first ServiceNow Table API response-status assertions:
  - `tests/test_servicenow.py::test_servicenow_table_api_rejects_response_object_without_leak`
  - `tests/test_servicenow.py::test_servicenow_table_api_rejects_status_code_object_without_leak`
  - `tests/test_servicenow.py::test_servicenow_table_api_rejects_status_code_outside_http_range[99]`
  - `tests/test_servicenow.py::test_servicenow_table_api_rejects_status_code_outside_http_range[600]`
- Initial failures proved regular Table API methods could execute hostile response/status hooks
  raising `client_secret=servicenow-table-response-object-secret` or
  `client_secret=servicenow-table-status-code-secret`, accepted status `99`, and routed status
  `600` into the ordinary API error path.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_697_documents_servicenow_table_api_status_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_raise_for_error()` as the shared ServiceNow API status branch helper.
- Regular Table API methods now use the shared exact response/status boundary before error
  formatting or result parsing.
- Existing redacted API error diagnostics are preserved after valid exact response/status
  validation passes.
- Verified `servicenow.py` no longer has raw `response.status_code` branches outside the hardened
  OAuth, probe, and shared helper paths.
- Documented the ServiceNow Table API response-status boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_table_api_rejects_response_object_without_leak or servicenow_table_api_rejects_status_code_object_without_leak or servicenow_table_api_rejects_status_code_outside_http_range"`
  failed first with 4 failures.
- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_table_api_rejects_response_object_without_leak or servicenow_table_api_rejects_status_code_object_without_leak or servicenow_table_api_rejects_status_code_outside_http_range or servicenow_api_failure_raises_without_secret_leakage or servicenow_api_error_body_dict_subclass_collapses_without_leak"`
  passed, 6 tests.
- `rg -n "if response\\.status_code|response\\.status_code >=" src/jedi_devproject/servicenow.py`
  returned no matches.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_697`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_696 or sprint_697"` passed,
  2 tests.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 230 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2966 tests with 93.26% total coverage.
