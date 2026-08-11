# Sprint 703 Change Log - ServiceNow field-list exact-list boundary

## Scope

Hardened ServiceNow Table API `sysparm_fields` construction so optional field lists must be exact
lists before field-name sanitization or transport activity.

## Tests First

- Added 1 failing-first ServiceNow field-list assertion:
  - `tests/test_servicenow.py::test_servicenow_client_rejects_table_record_fields_list_subclass_before_request`
- Initial failure proved `_servicenow_field_list()` iterated a list subclass while building
  `sysparm_fields`. The hostile fixture carried `client_secret=servicenow-field-list-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_703_documents_servicenow_field_list_exact_list_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `_servicenow_field_list()` now requires an exact list before field-name sanitization.
- `fetch_table_records()` rejects malformed field-list containers before OAuth token acquisition or
  GET request construction.
- Existing per-field validation for unsafe, oversized, non-string, and string-subclass field names
  remains in place for exact-list inputs.
- Documented the ServiceNow field-list exact-list boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "fields_list_subclass"` failed first with
  1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "fields_list_subclass"` passed, 1 test.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_703` passed, 1 test.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 246 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2988 tests with 93.27% total coverage.
