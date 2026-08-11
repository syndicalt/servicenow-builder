# Sprint 723 Change Log - ServiceNow transport response body read boundary

## Scope

Hardened ServiceNow urllib transport response body reads so successful response and HTTP error body
read failures leave the transport as a fixed `ServiceNowApiError` diagnostic before exact-bytes
validation, oversized-body checks, decoding, JSON parsing, diagnostic shaping, or internal
`HttpResponse` construction.

## Tests First

- Added 2 failing-first ServiceNow transport response body read assertions:
  - `tests/test_servicenow.py::test_urllib_transport_wraps_success_body_read_error_without_leak`
  - `tests/test_servicenow.py::test_urllib_transport_wraps_http_error_body_read_error_without_leak`
- Initial failures proved successful response read failures collapsed into the generic request-failure
  diagnostic and HTTP error body read failures escaped directly. The hostile fixtures carried
  `client_secret=servicenow-success-body-read-error-secret` and
  `client_secret=servicenow-error-body-read-error-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_723_documents_servicenow_transport_body_read_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_transport_read_response_body()` to wrap `.read()` execution with a fixed
  diagnostic before exact-bytes validation.
- `UrllibTransport.send()` now uses the safe read helper for successful urllib responses.
- `UrllibTransport.send()` now uses the safe read helper for HTTP error responses.
- Response body read failures now fail with `ServiceNow transport response body read failed` without
  stringifying or chaining the original exception.
- Documented the ServiceNow transport response body read boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "success_body_read_error or http_error_body_read_error"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_723` failed first with 1 failure.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q -k "success_body_read_error or http_error_body_read_error or success_body_bytes_subclass or http_error_body_bytes_subclass or rejects_oversized_success_response_body or returns_json_body_for_http_error_response"`
  passed with 6 tests and 274 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_723` passed with 1 test and 796
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 280 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3042 tests and 93.33% total coverage.
