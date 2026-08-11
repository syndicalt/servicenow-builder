# Sprint 695 Change Log - ServiceNow API error body top-level exact-dictionary boundary

## Scope

Hardened the ServiceNow API error diagnostic path so only exact dictionary error bodies enter rich
diagnostic shaping. This closes the remaining adjacent boundary after Sprint 694 validated the
response object and status code before API error formatting.

## Tests First

- Added 1 failing-first ServiceNow API error-body assertion:
  - `tests/test_servicenow.py::test_servicenow_api_error_body_dict_subclass_collapses_without_leak`
- Initial failure proved a top-level dict subclass error body could execute a hostile `items()` hook
  raising `client_secret=servicenow-error-body-items-secret` during API error diagnostic shaping.
- Added 1 regression assertion:
  - `tests/test_servicenow.py::test_servicenow_api_error_body_object_collapses_without_leak`
- The regression assertion confirmed arbitrary non-dictionary top-level bodies were already
  collapsed without calling hostile `repr()` hooks.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_695_documents_servicenow_api_error_body_top_level_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added a top-level API error diagnostic body helper.
- Exact dictionaries keep the existing ServiceNow API diagnostic redaction, key projection,
  duplicate-key handling, cycle safety, and final truncation behavior.
- Non-dictionary bodies and dict subclasses collapse to `[non-json value]` before diagnostic
  traversal, stringification, or reflection.
- Documented the ServiceNow API error-body boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_api_error_body_object_collapses_without_leak or servicenow_api_error_body_dict_subclass_collapses_without_leak"`
  failed first with 1 failure and 1 pass, proving the dict-subclass gap while confirming arbitrary
  non-dictionary bodies were already safe.
- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_api_error_body_object_collapses_without_leak or servicenow_api_error_body_dict_subclass_collapses_without_leak or servicenow_api_failure_raises_without_secret_leakage or servicenow_api_failure_bounds_final_error_diagnostic or servicenow_api_failure_redacts_secret_values"`
  passed, 4 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_695`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_694 or sprint_695"` passed,
  2 tests.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 223 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2957 tests with 93.19% total coverage.
