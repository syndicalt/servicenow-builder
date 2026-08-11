# Sprint 705 Change Log - ServiceNow dictionary max-length exact-int boundary

## Scope

Hardened ServiceNow dictionary-field request construction so `max_length` values must be exact
integers before comparison, string conversion, or transport activity.

## Tests First

- Added 1 failing-first ServiceNow dictionary max-length assertion:
  - `tests/test_servicenow.py::test_servicenow_client_rejects_story_dictionary_max_length_int_subclass_before_request`
- Initial failure proved `_servicenow_dictionary_max_length()` compared an `int` subclass while
  building a dictionary-field request. The hostile fixture carried
  `client_secret=servicenow-max-length-lt-secret` and
  `client_secret=servicenow-max-length-str-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_705_documents_servicenow_dictionary_max_length_exact_int_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `_servicenow_dictionary_max_length()` now requires an exact integer before range checks.
- `create_story_dictionary_field()` rejects boolean values, integer subclasses, non-integers, zero,
  negative values, and oversized max lengths with the existing fixed unsafe max-length diagnostic.
- Documented the ServiceNow dictionary max-length exact-int boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "max_length_int_subclass"` failed first with
  1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "dictionary_max_length or create_story_dictionary_field"`
  passed, 2 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_705` passed, 1 test.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 248 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2992 tests with 93.27% total coverage.
