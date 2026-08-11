# Sprint 711 Change Log - ServiceNow transport form body scalar boundary

## Scope

Hardened ServiceNow transport form-body encoding so non-JSON dictionary bodies must contain exact
string keys and exact string values before `urllib.parse.urlencode()` is called.

## Tests First

- Added 2 failing-first ServiceNow transport form body assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_form_body_string_subclass_key_before_urlencode`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_form_body_string_subclass_value_before_urlencode`
- Initial failures proved `UrllibTransport.send()` accepted string subclasses in form request body
  keys and values and proceeded to opener construction. The hostile fixtures carried
  `client_secret=servicenow-form-key-secret` and `client_secret=servicenow-form-value-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_711_documents_servicenow_transport_form_body_scalar_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_form_body()` to validate form-encoded request bodies before URL encoding.
- Non-JSON dictionary request bodies now require exact string keys and exact string values before
  `urllib.parse.urlencode()`.
- Malformed form body keys and values fail before URL encoding, implicit string conversion, opener
  construction, or raw `urllib` request construction.
- Valid OAuth/form posts using ordinary strings continue to encode as
  `application/x-www-form-urlencoded`.
- Documented the ServiceNow transport form body scalar boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "form_body_string_subclass"` failed first
  with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_711` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "form_body_string_subclass or encodes_query_and_form_body or body_bytes_subclass or headers_dict_subclass or body_dict_subclass or query_params_dict_subclass or non_finite_json_request_body or handles_request_without_params_or_body"`
  passed, 17 tests and 238 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_711` passed, 1 test and 784
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 255 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  3,005 tests with 93.28% total coverage.
