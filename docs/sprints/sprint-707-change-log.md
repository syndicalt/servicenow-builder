# Sprint 707 Change Log - ServiceNow transport query-params exact-dict boundary

## Scope

Hardened ServiceNow transport URL construction so `HttpRequest.params` must be an exact dictionary
before truthiness checks, URL encoding, or opener construction.

## Tests First

- Added 1 failing-first ServiceNow transport query-param assertion:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_query_params_dict_subclass_before_url_encoding`
- Initial failure proved `_url_with_params()` evaluated the truthiness of a dict subclass before URL
  encoding. The hostile fixture carried `client_secret=servicenow-query-params-len-secret` and
  `client_secret=servicenow-query-params-items-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_707_documents_servicenow_transport_query_params_exact_dict_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `_url_with_params()` now requires exact dictionary query params before empty checks.
- `UrllibTransport.send()` rejects malformed query-param containers before URL encoding or opener
  construction.
- Documented the ServiceNow transport query-params exact-dict boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "query_params_dict_subclass"` failed first with
  1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "query_params_dict_subclass or encodes_query_and_form_body"`
  passed, 2 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_707` passed, 1 test.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 250 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2996 tests with 93.27% total coverage.
