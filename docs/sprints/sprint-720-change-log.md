# Sprint 720 Change Log - ServiceNow transport network error boundary

## Scope

Hardened ServiceNow urllib transport network failure handling so non-HTTP urllib failures and local
socket/TLS `OSError` failures leave the transport as a fixed `ServiceNowApiError` diagnostic without
stringifying or chaining the original exception.

## Tests First

- Added 2 failing-first ServiceNow transport network error assertions:
  - `tests/test_servicenow.py::test_urllib_transport_wraps_url_error_without_reason_leak`
  - `tests/test_servicenow.py::test_urllib_transport_wraps_os_error_without_reason_leak`
- Initial failures proved `urllib.error.URLError` and `OSError` escaped the transport directly. The
  hostile fixtures carried `client_secret=servicenow-url-error-reason-secret` and
  `client_secret=servicenow-os-error-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_720_documents_servicenow_transport_network_error_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `UrllibTransport.send()` now catches non-HTTP `urllib.error.URLError` and local `OSError` failures
  after the bounded HTTP error path.
- Network failures now raise `ServiceNow transport request failed` with exception cause suppression.
- The transport does not read, stringify, or expose the original exception object or reason.
- HTTP error responses continue to use the bounded HTTP error response path.
- Documented the ServiceNow transport network error boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "wraps_url_error or wraps_os_error"` failed first
  with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_720` failed first with 1 failure.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files after the `URLError` hostile fixture was
  made a `BaseException` subclass.
- `python3 -m pytest tests/test_servicenow.py -q -k "wraps_url_error or wraps_os_error or returns_json_body_for_http_error_response or preserves_non_json_http_error_body"`
  passed with 4 tests and 270 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_720` passed with 1 test and 793
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 274 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3033 tests and 93.32% total coverage.
