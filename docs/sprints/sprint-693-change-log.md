# Sprint 693 Change Log - ServiceNow API response body exact-dictionary boundary

## Scope

Hardened the shared ServiceNow API success-response helper so deployment and CICD handoff responses
validate their JSON body as an exact dictionary before copying response data or adding
`status_code`.

## Tests First

- Added 2 failing-first ServiceNow API response-body assertions:
  - `tests/test_servicenow.py::test_servicenow_response_body_helper_rejects_body_object_without_leak`
  - `tests/test_servicenow.py::test_servicenow_response_body_helper_rejects_body_dict_subclass_without_leak`
- Initial failures proved a malformed response body could execute a hostile iteration hook raising
  `client_secret=servicenow-response-body-secret`, and a dict subclass carrying
  `client_secret=servicenow-response-dict-secret` was silently accepted.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_693_documents_servicenow_api_body_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `_servicenow_response_body_or_raise()` now requires successful response bodies to be exact
  dictionaries before copying them.
- Mapping-like body objects and dict subclasses fail with a fixed `ServiceNowApiError` diagnostic.
- Valid exact dictionaries are copied with the built-in `dict.copy()` before `status_code` metadata
  is appended.
- Documented the ServiceNow API body boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_response_body_helper_rejects_body_object_without_leak or servicenow_response_body_helper_rejects_body_dict_subclass_without_leak"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_response_body_helper_rejects_body_object_without_leak or servicenow_response_body_helper_rejects_body_dict_subclass_without_leak"`
  passed, 2 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_693`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_691 or sprint_692 or sprint_693"`
  passed, 3 tests.
- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_response_body_helper_rejects_body_object_without_leak or servicenow_response_body_helper_rejects_body_dict_subclass_without_leak or oauth_client_credentials_rejects_json_body_object_without_leak or oauth_client_credentials_rejects_json_body_dict_subclass_without_leak"`
  passed, 4 tests.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 217 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2949 tests with 93.16% total coverage.
