# Sprint 716 Change Log - ServiceNow transport query scalar boundary

## Scope

Hardened ServiceNow transport query parameter handling so `HttpRequest.params` entries must contain
exact string keys and exact string values before URL encoding, implicit string conversion, opener
construction, or raw request construction.

## Tests First

- Added 2 failing-first ServiceNow transport query scalar assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_query_param_key_string_subclass_before_urlencode`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_query_param_value_string_subclass_before_urlencode`
- Initial failures proved query parameter key and value string subclasses reached opener construction.
  The hostile fixtures carried `client_secret=servicenow-query-key-secret` and
  `client_secret=servicenow-query-value-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_716_documents_servicenow_transport_query_scalar_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_query_params()` to copy only exact string query parameter keys and exact string
  query parameter values.
- `_url_with_params()` now validates query parameter scalar values after the exact-dictionary
  container check and before `urllib.parse.urlencode()`.
- Malformed query parameter scalar values fail before URL encoding, implicit string conversion,
  opener construction, raw request construction, or credential-bearing scalar hooks can execute.
- Documented the ServiceNow transport query scalar boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "query_param_key_string_subclass or query_param_value_string_subclass"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_716` failed first with 1 failure.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q -k "query_param_key_string_subclass or query_param_value_string_subclass or query_params_dict_subclass or encodes_query_and_form_body or method_string_subclass or url_string_subclass or credentialed_url or header_key_string_subclass or header_value_string_subclass"`
  passed with 9 tests and 257 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_716` passed with 1 test and 789
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 266 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3021 tests and 93.31% total coverage.
