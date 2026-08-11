# Sprint 696 Change Log - ServiceNow Table API result body exact-dictionary boundary

## Scope

Hardened the ServiceNow Table API result extraction helpers so response bodies must be exact
dictionaries before `result` lookup for both list-returning and object-returning client methods.

## Tests First

- Added 3 failing-first ServiceNow result-body assertions:
  - `tests/test_servicenow.py::test_servicenow_result_record_list_rejects_body_object_without_leak`
  - `tests/test_servicenow.py::test_servicenow_result_record_list_rejects_body_dict_subclass_without_leak`
  - `tests/test_servicenow.py::test_servicenow_result_object_rejects_body_dict_subclass_without_leak`
- Initial failures proved result extraction could execute hostile `get()` hooks raising
  `client_secret=servicenow-result-body-secret`,
  `client_secret=servicenow-result-dict-secret`, or
  `client_secret=servicenow-result-object-dict-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_696_documents_servicenow_result_body_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added a shared result-body boundary helper for ServiceNow Table API parsing.
- `_required_result_record_list()` and `_required_result_object()` now require exact dictionary
  response bodies before `result` extraction.
- Existing result-shape diagnostics for non-list results, non-object record entries, and
  non-object result values are preserved after the top-level body boundary passes.
- Documented the ServiceNow Table API result-body boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_result_record_list_rejects_body_object_without_leak or servicenow_result_record_list_rejects_body_dict_subclass_without_leak or servicenow_result_object_rejects_body_dict_subclass_without_leak"`
  failed first with 3 failures.
- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_result_record_list_rejects_body_object_without_leak or servicenow_result_record_list_rejects_body_dict_subclass_without_leak or servicenow_result_object_rejects_body_dict_subclass_without_leak or servicenow_success_result_list_shape_error_does_not_echo_result_value or servicenow_success_result_record_shape_error_does_not_echo_result_value or servicenow_success_result_object_shape_error_does_not_echo_result_value"`
  passed, 6 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_696`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_695 or sprint_696"` passed,
  2 tests.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 226 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2961 tests with 93.19% total coverage.
