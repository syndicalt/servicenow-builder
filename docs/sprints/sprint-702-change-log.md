# Sprint 702 Change Log - ServiceNow lookup body exact-dict boundary

## Scope

Hardened ServiceNow Table API lookup query construction so submitted lookup bodies must be exact
dictionaries before lookup key/value sanitization or transport activity.

## Tests First

- Added 2 failing-first ServiceNow lookup-body assertions:
  - `tests/test_servicenow.py::test_servicenow_client_rejects_lookup_dict_subclass_before_request`
  - `tests/test_servicenow.py::test_servicenow_client_rejects_upsert_lookup_dict_subclass_before_lookup`
- Initial failures proved `_servicenow_lookup_query()` called a dict subclass `items()` hook while
  building lookup queries. The hostile fixtures carried
  `client_secret=servicenow-lookup-body-secret` and
  `client_secret=servicenow-upsert-lookup-body-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_702_documents_servicenow_lookup_body_exact_dict_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `_servicenow_lookup_query()` now requires an exact dictionary before lookup key/value
  sanitization.
- `fetch_table_record()` and `fetch_table_records()` reject malformed lookup bodies before OAuth
  token acquisition or GET request construction.
- `upsert_table_record()` rejects malformed lookup bodies before lookup GET requests, POST requests,
  or PATCH requests.
- Documented the ServiceNow lookup-body exact-dict boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "lookup_dict_subclass"` failed first with
  2 failures.
- `python3 -m pytest tests/test_servicenow.py -q -k "lookup_dict_subclass"` passed, 2 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_702` passed, 1 test.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 245 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2986 tests with 93.27% total coverage.
