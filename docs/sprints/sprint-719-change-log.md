# Sprint 719 Change Log - ServiceNow transport response body bytes boundary

## Scope

Hardened ServiceNow urllib transport response-body handling so successful response reads and HTTP
error response reads must return exact bytes before length checks, decoding, JSON parsing, diagnostic
shaping, or internal `HttpResponse` construction.

## Tests First

- Added 2 failing-first ServiceNow transport response body bytes assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_success_body_bytes_subclass_before_decode`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_http_error_body_bytes_subclass_before_parse`
- Initial corrected failures proved successful response and HTTP error response bytes subclasses
  reached decode. The hostile fixtures carried
  `client_secret=servicenow-success-body-decode-secret` and
  `client_secret=servicenow-error-body-decode-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_719_documents_servicenow_transport_response_body_bytes_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_transport_response_body()` to accept only exact bytes returned by transport
  `.read()` calls.
- `UrllibTransport.send()` now validates successful response bodies immediately after `response.read()`
  and before oversized-body checks or JSON decoding.
- `UrllibTransport.send()` now validates HTTP error response bodies immediately after `exc.read()`
  and before oversized-error checks or diagnostic parsing.
- Malformed response body values fail before length checks, decoding, JSON parsing, diagnostic
  shaping, model construction, or credential-bearing decode hooks can execute.
- Documented the ServiceNow transport response body bytes boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "success_body_bytes_subclass or http_error_body_bytes_subclass"`
  failed first with 2 failures after correcting the fake response fixtures to return the bytes
  subclass directly from `.read()`.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_719` failed first with 1 failure.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q -k "success_body_bytes_subclass or http_error_body_bytes_subclass or rejects_oversized_success_response_body or returns_json_body_for_http_error_response or rejects_non_finite_http_error_json"`
  passed with 5 tests and 267 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_719` passed with 1 test and 792
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 272 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3030 tests and 93.32% total coverage.
