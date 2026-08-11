# Sprint 710 Change Log - ServiceNow transport body-bytes exact-bytes boundary

## Scope

Hardened ServiceNow transport raw body handling so `HttpRequest.body_bytes` must be exact bytes before
opener construction or raw `urllib` request construction.

## Tests First

- Added 1 failing-first ServiceNow transport body-bytes assertion:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_body_bytes_subclass_before_opening`
- Initial failure proved `UrllibTransport.send()` accepted a bytes subclass as raw request data and
  proceeded to opener construction. The hostile fixture carried
  `client_secret=servicenow-body-bytes-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_710_documents_servicenow_transport_body_bytes_exact_bytes_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `UrllibTransport.send()` now requires exact bytes for `HttpRequest.body_bytes` when supplied.
- Malformed raw body payloads fail before opener construction or raw `urllib` request construction.
- Valid attachment uploads that pass ordinary bytes continue to bypass dictionary body encoding.
- Documented the ServiceNow transport body-bytes exact-bytes boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "body_bytes_subclass"` failed first with
  1 failure.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_710` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "body_bytes_subclass or uploads_story_attachment_with_binary_body or headers_dict_subclass or body_dict_subclass or query_params_dict_subclass or encodes_query_and_form_body or non_finite_json_request_body or handles_request_without_params_or_body"`
  passed, 16 tests and 237 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_710` passed, 1 test and 783
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 253 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  3,002 tests with 93.28% total coverage.
