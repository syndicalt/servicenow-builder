# Sprint 708 Change Log - ServiceNow transport request-body exact-dict boundary

## Scope

Hardened ServiceNow transport body encoding so `HttpRequest.body` must be an exact dictionary before
truthiness checks, JSON serialization, form encoding, or opener construction.

## Tests First

- Added 1 failing-first ServiceNow transport body assertion:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_body_dict_subclass_before_encoding`
- Initial failure proved `UrllibTransport.send()` evaluated the truthiness of a dict subclass before
  choosing JSON or form encoding. The hostile fixture carried `client_secret=servicenow-body-len-secret`
  and `client_secret=servicenow-body-items-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_708_documents_servicenow_transport_body_exact_dict_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `UrllibTransport.send()` now requires exact dictionary request bodies when `body_bytes` is not
  supplied.
- Malformed request body containers fail before truthiness checks, JSON serialization, form encoding,
  or opener construction.
- Raw attachment upload paths using `body_bytes` continue to bypass dictionary body encoding.
- Documented the ServiceNow transport request-body exact-dict boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "body_dict_subclass"` failed first with
  1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "body_dict_subclass or encodes_query_and_form_body or non_finite_json_request_body or handles_request_without_params_or_body"`
  passed, 12 tests.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 251 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_708` passed, 1 test and 781
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2,998 tests with 93.28% total coverage.
