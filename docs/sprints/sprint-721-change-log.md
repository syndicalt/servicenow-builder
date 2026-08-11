# Sprint 721 Change Log - ServiceNow transport status-before-body boundary

## Scope

Hardened ServiceNow urllib transport response handling so successful response `status` values and
HTTP error `code` values are validated before response body reads.

## Tests First

- Added 2 failing-first ServiceNow transport status-before-body assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_success_status_before_body_read`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_http_error_code_before_body_read`
- Initial failures proved successful responses and HTTP error responses read bodies before rejecting
  malformed status values. The hostile fixtures carried
  `client_secret=servicenow-success-body-read-secret` and
  `client_secret=servicenow-error-body-read-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_721_documents_servicenow_transport_status_before_body_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `UrllibTransport.send()` now validates successful response `status` values before `response.read()`.
- `UrllibTransport.send()` now validates HTTP error `code` values before `exc.read()`.
- The validated status code is reused for internal `HttpResponse` construction.
- Malformed status values fail before body streaming, oversized-body checks, decoding, diagnostic
  shaping, model construction, or credential-bearing body read hooks can execute.
- Documented the ServiceNow transport status-before-body boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "success_status_before_body_read or http_error_code_before_body_read"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_721` failed first with 1 failure.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q -k "success_status_before_body_read or http_error_code_before_body_read or success_status_int_subclass or http_error_code_int_subclass or returns_json_body_for_http_error_response"`
  passed with 5 tests and 271 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_721` passed with 1 test and 794
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 276 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3036 tests and 93.32% total coverage.
