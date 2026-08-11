# Sprint 728 Change Log - ServiceNow transport URL encoding boundary

## Scope

Hardened ServiceNow urllib transport URL encoding so unexpected query-string or form-body
`urllib.parse.urlencode()` failures leave the transport as a fixed `ServiceNowApiError`
diagnostic without leaking credential-bearing encoder exception text.

## Tests First

- Added 2 failing-first ServiceNow transport URL encoding assertions:
  - `tests/test_servicenow.py::test_urllib_transport_wraps_query_urlencode_error_without_leak`
  - `tests/test_servicenow.py::test_urllib_transport_wraps_form_urlencode_error_without_leak`
- Initial failures proved query and form URL encoding escaped directly before raw request
  construction. The hostile fixtures carried `client_secret=servicenow-query-urlencode-secret` and
  `client_secret=servicenow-form-urlencode-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_728_documents_servicenow_transport_url_encoding_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_transport_urlencode()` as the single safe boundary for raw urllib URL encoding.
- Routed query parameter and form body encoding through the safe helper after existing exact-container
  and exact-string scalar validation.
- Wrapped URL-encoding failures as `ServiceNow transport URL encoding failed` without stringifying or
  chaining the original exception.
- Preserved the existing validation-before-encoding checks for query params and form body fields.
- Documented the ServiceNow transport URL encoding boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "query_urlencode_error or form_urlencode_error"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_728` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "query_urlencode_error or form_urlencode_error or encodes_query_and_form_body or query_param_key_string_subclass or form_body_string_subclass"`
  passed with 6 tests and 282 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_728` passed with 1 test and 801
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 288 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3055 tests and 93.33% total coverage.
