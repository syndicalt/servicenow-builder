# Sprint 709 Change Log - ServiceNow transport headers exact-dict boundary

## Scope

Hardened ServiceNow transport header handling so `HttpRequest.headers` must be an exact dictionary
before header copying, `Content-Type` lookup, body encoding decisions, opener construction, or raw
`urllib` request construction.

## Tests First

- Added 1 failing-first ServiceNow transport headers assertion:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_headers_dict_subclass_before_encoding`
- Initial failure proved `UrllibTransport.send()` accepted a dict subclass as request headers and
  proceeded to opener construction. The hostile fixture carried
  `client_secret=servicenow-headers-items-secret` and
  `client_secret=servicenow-headers-get-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_709_documents_servicenow_transport_headers_exact_dict_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `UrllibTransport.send()` now requires exact dictionary request headers before copying or using
  them.
- Malformed request header containers fail before `Content-Type` lookup, JSON serialization, form
  encoding, opener construction, or raw `urllib` request construction.
- Documented the ServiceNow transport headers exact-dict boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "headers_dict_subclass"` failed first with
  1 failure.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_709` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "headers_dict_subclass or body_dict_subclass or query_params_dict_subclass or encodes_query_and_form_body or non_finite_json_request_body or handles_request_without_params_or_body"`
  passed, 14 tests and 238 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_709` passed, 1 test and 782
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 252 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  3,000 tests with 93.28% total coverage.
