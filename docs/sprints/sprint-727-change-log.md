# Sprint 727 Change Log - ServiceNow transport request construction boundary

## Scope

Hardened ServiceNow urllib transport raw request construction so unexpected
`urllib.request.Request(...)` failures leave the transport as a fixed `ServiceNowApiError`
diagnostic without leaking credential-bearing constructor exception text.

## Tests First

- Added 1 failing-first ServiceNow transport request construction assertion:
  `tests/test_servicenow.py::test_urllib_transport_wraps_request_construction_error_without_leak`
- Initial failure proved raw request construction escaped directly before opener construction and
  request execution boundaries. The hostile fixture carried
  `client_secret=servicenow-request-construction-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_727_documents_servicenow_transport_request_construction_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_transport_request()` as the single safe boundary for raw urllib request
  construction.
- Wrapped request-construction failures as `ServiceNow transport request failed` without
  stringifying or chaining the original exception.
- Preserved the existing validation-before-construction checks for method, URL, query, headers,
  body, and timeout values.
- Preserved the existing safe opener construction, opener execution, response context, status,
  body-read, and HTTP error paths.
- Documented the ServiceNow transport request construction boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k request_construction_error` failed first with 1
  failure.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_727` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "request_construction_error or build_opener_error or unexpected_open_error or open_attribute_error or encodes_query_and_form_body or sends_json_body"`
  passed with 5 tests and 281 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_727` passed with 1 test and 800
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 286 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3052 tests and 93.33% total coverage.
