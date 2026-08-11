# Sprint 713 Change Log - ServiceNow transport JSON body recursion boundary

## Scope

Hardened ServiceNow transport JSON request-body validation so recursive exact-JSON traversal is
cycle-safe and depth-bounded before `json.dumps()` or opener construction.

## Tests First

- Added 2 failing-first ServiceNow transport JSON recursion assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_circular_json_body_before_serialization`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_deep_json_body_before_serialization`
- Initial failures proved a circular dictionary caused a raw `RecursionError`, while a deeply nested
  dictionary payload proceeded to opener construction.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_713_documents_servicenow_transport_json_body_recursion_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `MAX_SERVICENOW_JSON_REQUEST_BODY_DEPTH` with a 100-container depth cap.
- `_servicenow_json_body()` now tracks active exact list and dictionary container ids while
  recursively validating request bodies.
- Cyclic JSON request bodies fail with
  `ServiceNow JSON request body contains circular references`.
- Over-depth JSON request bodies fail with `ServiceNow JSON request body is too deeply nested`.
- Existing exact-JSON scalar validation and non-finite numeric diagnostics remain unchanged.
- Documented the ServiceNow transport JSON body recursion boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "circular_json_body or deep_json_body"` failed
  first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_713` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "circular_json_body or deep_json_body or json_body_string_subclass_key or json_body_non_json_value or non_finite_json_request_body or form_body_string_subclass or encodes_query_and_form_body or body_bytes_subclass or headers_dict_subclass or body_dict_subclass or query_params_dict_subclass or handles_request_without_params_or_body"`
  passed, 21 tests and 238 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_713` passed, 1 test and 786
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 259 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  3,011 tests with 93.29% total coverage.
