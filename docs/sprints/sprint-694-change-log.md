# Sprint 694 Change Log - ServiceNow API response status boundary

## Scope

Hardened the shared ServiceNow API response helper so CICD progress, update-set import, and update
set action responses validate the transport response object and status code before success/failure
branching or diagnostic formatting.

## Tests First

- Added 4 failing-first ServiceNow API response-status assertions:
  - `tests/test_servicenow.py::test_servicenow_response_body_helper_rejects_response_object_without_leak`
  - `tests/test_servicenow.py::test_servicenow_response_body_helper_rejects_status_code_object_without_leak`
  - `tests/test_servicenow.py::test_servicenow_response_body_helper_rejects_status_code_outside_http_range[99]`
  - `tests/test_servicenow.py::test_servicenow_response_body_helper_rejects_status_code_outside_http_range[600]`
- Initial failures proved malformed response objects could execute hostile `status_code` attribute
  hooks raising `client_secret=servicenow-api-response-object-secret`, status-code objects could
  execute comparison hooks raising `client_secret=servicenow-api-status-code-secret`, status `99`
  was accepted, and status `600` entered the normal API error diagnostic path.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_694_documents_servicenow_api_response_status_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added a shared ServiceNow API response status helper for `_servicenow_response_body_or_raise()`.
- Shared ServiceNow API responses must be exact `HttpResponse` objects before status access.
- Shared ServiceNow API status codes must be exact integers in the HTTP `100..599` range before
  comparison or API error formatting.
- Existing API failure diagnostics still include the validated integer status and redacted body
  context.
- Documented the ServiceNow API response/status boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_response_body_helper_rejects_response_object_without_leak or servicenow_response_body_helper_rejects_status_code_object_without_leak or servicenow_response_body_helper_rejects_status_code_outside_http_range"`
  failed first with 4 failures.
- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_response_body_helper_rejects_response_object_without_leak or servicenow_response_body_helper_rejects_status_code_object_without_leak or servicenow_response_body_helper_rejects_status_code_outside_http_range or servicenow_response_body_helper_rejects_body_object_without_leak or servicenow_response_body_helper_rejects_body_dict_subclass_without_leak or servicenow_api_failure_raises_without_secret_leakage"`
  passed, 7 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_694`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_693 or sprint_694"` passed,
  2 tests.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 221 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2954 tests with 93.17% total coverage.
