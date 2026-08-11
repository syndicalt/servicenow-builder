# Sprint 706 Change Log - ServiceNow lookup response scalar exact-type boundary

## Scope

Hardened ServiceNow lookup response scalar handling so existing-record values reused for follow-on
requests cannot execute subclass stringification hooks.

## Tests First

- Added 1 failing-first ServiceNow lookup-response assertion:
  - `tests/test_servicenow.py::test_servicenow_client_upsert_rejects_existing_record_sys_id_int_subclass`
- Initial failure proved `_servicenow_lookup_text()` stringified an `int` subclass while extracting
  an existing-record `sys_id` for generic table upsert. The hostile fixture carried
  `client_secret=servicenow-lookup-response-int-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_706_documents_servicenow_lookup_response_scalar_exact_type_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `_servicenow_lookup_text()` now accepts only null, exact strings, exact booleans, and exact
  integers before record-id validation.
- Generic table upsert rejects string subclasses, integer subclasses, arbitrary objects, and other
  non-JSON scalar values before PATCH URL construction.
- Documented the ServiceNow lookup response scalar exact-type boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "sys_id_int_subclass"` failed first with
  1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "existing_record_sys_id"` passed, 3 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_706` passed, 1 test.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 249 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2994 tests with 93.27% total coverage.
