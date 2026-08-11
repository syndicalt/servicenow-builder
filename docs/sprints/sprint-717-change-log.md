# Sprint 717 Change Log - ServiceNow transport response status boundary

## Scope

Hardened ServiceNow urllib transport response handling so successful response `status` values and
HTTP error `code` values must be exact HTTP status integers before internal `HttpResponse`
construction.

## Tests First

- Added 2 failing-first ServiceNow transport response status assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_success_status_int_subclass_without_leak`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_http_error_code_int_subclass_without_leak`
- Initial failures proved success response status and HTTP error code integer subclasses were accepted
  into `HttpResponse`. The hostile fixtures carried
  `client_secret=servicenow-success-status-lt-secret` and
  `client_secret=servicenow-http-error-code-gt-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_717_documents_servicenow_transport_response_status_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_transport_response_status()` to accept only exact integer status values in the
  HTTP `100..599` range.
- `UrllibTransport.send()` now validates successful urllib response `status` values before internal
  `HttpResponse` construction.
- `UrllibTransport.send()` now validates HTTP error `code` values before oversized-error or parsed
  error `HttpResponse` construction.
- Malformed response status values fail before model coercion, downstream response branching, or
  credential-bearing status hooks can execute.
- Documented the ServiceNow transport response status boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "success_status_int_subclass or http_error_code_int_subclass"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_717` failed first with 1 failure.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q -k "success_status_int_subclass or http_error_code_int_subclass or returns_json_body_for_http_error_response or rejects_non_finite_http_error_json or rejects_oversized_success_response_body or encodes_query_and_form_body"`
  passed with 6 tests and 262 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_717` passed with 1 test and 790
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 268 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3024 tests and 93.31% total coverage.
