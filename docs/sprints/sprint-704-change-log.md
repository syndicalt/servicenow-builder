# Sprint 704 Change Log - ServiceNow result-limit exact-int boundary

## Scope

Hardened ServiceNow Table API result-limit request construction so `sysparm_limit` values must be
exact integers before comparison, string conversion, or transport activity.

## Tests First

- Added 1 failing-first ServiceNow result-limit assertion:
  - `tests/test_servicenow.py::test_servicenow_client_rejects_result_limit_int_subclass_before_request`
- Initial failure proved `_servicenow_result_limit()` compared an `int` subclass while building
  `sysparm_limit`. The hostile fixture carried
  `client_secret=servicenow-result-limit-lt-secret` and
  `client_secret=servicenow-result-limit-str-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_704_documents_servicenow_result_limit_exact_int_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `_servicenow_result_limit()` now requires an exact integer before range checks.
- Story queries and table-record list queries reject boolean values, integer subclasses,
  non-integers, zero, negative values, and oversized values with the existing fixed unsafe-limit
  diagnostic.
- Documented the ServiceNow result-limit exact-int boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "result_limit_int_subclass"` failed first with
  1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "result_limit or table_record_limit or fetch_stories_rejects_invalid_limit"`
  passed, 2 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_704` passed, 1 test.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 247 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2990 tests with 93.27% total coverage.
