# Sprint 722 Change Log - ServiceNow transport status attribute boundary

## Scope

Hardened ServiceNow urllib transport response status access so successful response `status` and HTTP
error `code` attributes are read through a safe boundary before value validation, body reads, or
diagnostic shaping.

## Tests First

- Added 2 failing-first ServiceNow transport status attribute assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_success_status_attribute_error_without_leak`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_http_error_code_attribute_error_without_leak`
- Initial failures proved successful response `status` and HTTP error `code` attribute lookup could
  execute hostile hooks before fixed status diagnostics. The hostile fixtures carried
  `client_secret=servicenow-success-status-attr-secret` and
  `client_secret=servicenow-http-error-code-attr-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_722_documents_servicenow_transport_status_attribute_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_transport_response_status_attribute()` to read `status` or `code` attributes
  through a fixed-diagnostic boundary.
- `UrllibTransport.send()` now uses the safe status attribute reader for successful urllib responses.
- `UrllibTransport.send()` now uses the safe status attribute reader for HTTP error responses.
- Status attribute lookup failures fail before value validation, body reads, diagnostic shaping, or
  credential-bearing attribute hooks can escape.
- Documented the ServiceNow transport status attribute boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "success_status_attribute_error or http_error_code_attribute_error"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_722` failed first with 1 failure.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q -k "success_status_attribute_error or http_error_code_attribute_error or success_status_before_body_read or http_error_code_before_body_read or success_status_int_subclass or http_error_code_int_subclass"`
  passed with 6 tests and 272 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_722` passed with 1 test and 795
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 278 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3039 tests and 93.32% total coverage.
