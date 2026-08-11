# Sprint 701 Change Log - ServiceNow mutation field-body exact-dict boundary

## Scope

Hardened ServiceNow Table API mutation request construction so submitted field bodies must be exact
dictionaries before field-name sanitization or transport activity.

## Tests First

- Added 2 failing-first ServiceNow field-body assertions:
  - `tests/test_servicenow.py::test_servicenow_client_rejects_story_patch_field_body_dict_subclass_before_request`
  - `tests/test_servicenow.py::test_servicenow_client_rejects_upsert_field_body_dict_subclass_before_lookup`
- Initial failures proved `_servicenow_field_body()` called a dict subclass `items()` hook while
  building story update and generic upsert bodies. The hostile fixtures carried
  `client_secret=servicenow-field-body-secret` and
  `client_secret=servicenow-upsert-field-body-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_701_documents_servicenow_mutation_field_body_exact_dict_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `_servicenow_field_body()` now requires an exact dictionary before field-name sanitization.
- `update_story_fields()` rejects malformed field bodies before OAuth token acquisition or PATCH
  request construction.
- `upsert_table_record()` rejects malformed field bodies before lookup queries, OAuth token
  acquisition, POST requests, or PATCH requests.
- Documented the ServiceNow mutation field-body exact-dict boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "field_body_dict_subclass"` failed first with
  2 failures.
- `python3 -m pytest tests/test_servicenow.py -q -k "field_body_dict_subclass"` passed, 2 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_701` passed, 1 test.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 243 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2983 tests with 93.27% total coverage.
