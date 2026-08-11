# Sprint 725 Change Log - ServiceNow transport opener boundary

## Scope

Hardened ServiceNow urllib transport opener execution so unexpected `opener.open()` failures
leave the transport as a fixed `ServiceNowApiError` diagnostic without leaking credential-bearing
opener exception text.

## Tests First

- Added 2 failing-first ServiceNow transport opener assertions:
  - `tests/test_servicenow.py::test_urllib_transport_wraps_unexpected_open_error_without_leak`
  - `tests/test_servicenow.py::test_urllib_transport_wraps_open_attribute_error_without_leak`
- Initial failures proved unexpected opener execution and hostile `open` attribute lookup failures
  escaped directly. The hostile fixtures carried `client_secret=servicenow-open-runtime-secret` and
  `client_secret=servicenow-open-attr-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_725_documents_servicenow_transport_opener_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_transport_open()` as the single safe boundary for raw urllib opener execution.
- Preserved `urllib.error.HTTPError` behavior so HTTP error responses still flow through bounded
  status and body handling.
- Wrapped every other opener execution failure as `ServiceNow transport request failed` without
  stringifying or chaining the original exception.
- Documented the ServiceNow transport opener boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "unexpected_open_error or open_attribute_error"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_725` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "unexpected_open_error or open_attribute_error or wraps_url_error_without_reason_leak or wraps_os_error_without_reason_leak or returns_json_body_for_http_error_response"`
  passed with 5 tests and 279 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_725` passed with 1 test and 798
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 284 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3048 tests and 93.33% total coverage.
