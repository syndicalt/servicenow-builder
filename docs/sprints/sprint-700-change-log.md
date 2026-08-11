# Sprint 700 Change Log - ServiceNow result payload exact-container boundary

## Scope

Hardened ServiceNow Table API success-result parsing so nested `result` containers must be exact
JSON-compatible Python containers before record mapping or result-object return.

## Tests First

- Added 3 failing-first ServiceNow result-container assertions:
  - `tests/test_servicenow.py::test_servicenow_result_record_list_rejects_list_subclass_without_leak`
  - `tests/test_servicenow.py::test_servicenow_result_record_list_rejects_entry_dict_subclass_without_leak`
  - `tests/test_servicenow.py::test_servicenow_result_object_rejects_result_dict_subclass_without_leak`
- Initial failures proved the Table API path could traverse a list subclass, call `get()` on a dict
  subclass record, or accept a dict subclass result object. The hostile fixtures carried
  `client_secret=servicenow-result-list-secret`, `client_secret=servicenow-result-record-secret`,
  and `client_secret=servicenow-result-object-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_700_documents_servicenow_result_payload_exact_container_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `_required_result_record_list()` preserves existing diagnostics for ordinary non-list and
  non-object JSON result shapes, then rejects list subclasses and record dict subclasses with fixed
  exact-container diagnostics.
- `_required_result_object()` preserves the existing diagnostic for ordinary non-object result
  shapes, then rejects result dict subclasses with a fixed exact-object diagnostic.
- Documented the ServiceNow Table API `result` exact-container boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "result_record_list_rejects or result_object_rejects_result"`
  failed first with 3 production failures and 1 missing test-import failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "result_record_list_rejects or result_object_rejects_result"`
  passed, 5 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_700` passed, 1 test.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 241 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2980 tests with 93.27% total coverage.
