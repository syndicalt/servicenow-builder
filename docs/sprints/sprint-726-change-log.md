# Sprint 726 Change Log - ServiceNow transport opener construction boundary

## Scope

Hardened ServiceNow urllib transport opener construction so unexpected
`urllib.request.build_opener()` failures leave the transport as a fixed `ServiceNowApiError`
diagnostic without leaking credential-bearing construction exception text.

## Tests First

- Added 1 failing-first ServiceNow transport opener construction assertion:
  `tests/test_servicenow.py::test_urllib_transport_wraps_build_opener_error_without_leak`
- Initial failure proved opener construction escaped directly before the request-failed boundary.
  The hostile fixture carried `client_secret=servicenow-build-opener-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_726_documents_servicenow_transport_opener_construction_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_transport_build_opener()` as the single safe boundary for raw urllib opener
  construction.
- Wrapped opener-construction failures as `ServiceNow transport request failed` without stringifying
  or chaining the original exception.
- Preserved the existing safe opener execution, response context, status, body-read, and HTTP error
  paths.
- Documented the ServiceNow transport opener construction boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k build_opener_error` failed first with 1 failure.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_726` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "build_opener_error or unexpected_open_error or open_attribute_error or wraps_url_error_without_reason_leak or wraps_os_error_without_reason_leak or returns_json_body_for_http_error_response"`
  passed with 6 tests and 279 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_726` passed with 1 test and 799
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 285 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3050 tests and 93.33% total coverage.
