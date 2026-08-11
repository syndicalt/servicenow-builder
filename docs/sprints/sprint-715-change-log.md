# Sprint 715 Change Log - ServiceNow transport header scalar boundary

## Scope

Hardened ServiceNow transport header handling so `HttpRequest.headers` entries must contain exact
string keys and exact string values before header copying, `Content-Type` lookup, raw `urllib`
request construction, or opener construction.

## Tests First

- Added 2 failing-first ServiceNow transport header scalar assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_header_key_string_subclass_before_request_construction`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_header_value_string_subclass_before_request`
- Initial failures proved header key and value string subclasses reached opener construction. The
  hostile fixtures carried `client_secret=servicenow-header-key-title-secret` and
  `client_secret=servicenow-header-value-title-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_715_documents_servicenow_transport_header_scalar_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_request_headers()` to copy only exact string header keys and exact string header
  values.
- `UrllibTransport.send()` now validates header scalar values immediately after the exact-dictionary
  container check.
- Malformed header scalar values fail before `Content-Type` lookup, raw `urllib` request
  construction, opener construction, or credential-bearing scalar hooks can execute.
- Documented the ServiceNow transport header scalar boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "header_key_string_subclass or header_value_string_subclass"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_715` failed first with 1 failure.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q -k "header_key_string_subclass or header_value_string_subclass or headers_dict_subclass or method_string_subclass or url_string_subclass or credentialed_url or encodes_query_and_form_body or body_bytes_subclass or handles_request_without_params_or_body"`
  passed with 9 tests and 255 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_715` passed with 1 test and 788
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 264 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3018 tests and 93.31% total coverage.
