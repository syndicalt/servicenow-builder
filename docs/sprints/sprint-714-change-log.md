# Sprint 714 Change Log - ServiceNow transport method and URL boundary

## Scope

Hardened ServiceNow transport request construction so `HttpRequest.method` and `HttpRequest.url` are
validated before query encoding, raw `urllib` request construction, or opener construction.

## Tests First

- Added 2 failing-first ServiceNow transport method/URL assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_method_string_subclass_before_request_construction`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_url_string_subclass_before_request_construction`
- Initial failures proved method and URL string subclasses reached opener construction. The hostile
  fixtures carried `client_secret=servicenow-method-upper-secret` and
  `client_secret=servicenow-url-encode-secret`.
- Added 1 additional URL safety assertion:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_credentialed_url_before_request_construction`
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_714_documents_servicenow_transport_method_url_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_request_method()` to require exact supported uppercase HTTP methods.
- Added `_servicenow_request_url()` to require exact absolute HTTP or HTTPS URLs with no embedded
  credentials, fragments, whitespace/control characters, decoded whitespace/control characters, or
  oversized values.
- `UrllibTransport.send()` validates method and URL before query encoding and raw request
  construction.
- Documented the ServiceNow transport method and URL boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "method_string_subclass or url_string_subclass"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_714` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "method_string_subclass or url_string_subclass or credentialed_url or encodes_query_and_form_body or query_params_dict_subclass or circular_json_body or deep_json_body or body_bytes_subclass or headers_dict_subclass or handles_request_without_params_or_body"`
  passed, 10 tests and 252 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_714` passed, 1 test and 787
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 262 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  3,015 tests with 93.30% total coverage.
