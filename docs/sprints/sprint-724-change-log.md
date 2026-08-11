# Sprint 724 Change Log - ServiceNow transport response context boundary

## Scope

Hardened ServiceNow urllib transport successful-response context handling so response context
`__enter__` and `__exit__` failures leave the transport as a fixed `ServiceNowApiError` diagnostic
without leaking credential-bearing context hook text.

## Tests First

- Added 2 failing-first ServiceNow transport response context assertions:
  - `tests/test_servicenow.py::test_urllib_transport_wraps_success_context_enter_error_without_leak`
  - `tests/test_servicenow.py::test_urllib_transport_wraps_success_context_exit_error_without_leak`
- Initial failures proved successful response `__enter__` and `__exit__` failures escaped directly.
  The hostile fixtures carried `client_secret=servicenow-success-enter-secret` and
  `client_secret=servicenow-success-exit-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_724_documents_servicenow_transport_response_context_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Replaced the implicit successful-response `with` block with explicit safe context enter and exit
  helpers.
- Added `_servicenow_transport_enter_response_context()` to wrap response `__enter__` failures.
- Added `_servicenow_transport_exit_response_context()` to wrap response `__exit__` failures on both
  normal and exceptional response processing paths.
- Context failures now fail with `ServiceNow transport response context failed` without stringifying
  or chaining the original exception.
- Documented the ServiceNow transport response context boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "success_context_enter_error or success_context_exit_error"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_724` failed first with 1 failure.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q -k "success_context_enter_error or success_context_exit_error or encodes_query_and_form_body or returns_json_body_for_http_error_response or success_body_read_error"`
  passed with 5 tests and 277 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_724` passed with 1 test and 797
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 282 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3045 tests and 93.33% total coverage.
