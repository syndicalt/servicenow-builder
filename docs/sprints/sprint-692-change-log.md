# Sprint 692 Change Log - ServiceNow OAuth response body exact-dictionary boundary

## Scope

Hardened ServiceNow OAuth token acquisition so the token response body is validated as an exact
dictionary before access-token lookup. Sprint 691 validated the response object and status code;
this sprint closes the adjacent body shape boundary.

## Tests First

- Added 2 failing-first ServiceNow OAuth body assertions:
  - `tests/test_servicenow.py::test_oauth_client_credentials_rejects_json_body_object_without_leak`
  - `tests/test_servicenow.py::test_oauth_client_credentials_rejects_json_body_dict_subclass_without_leak`
- Initial failures proved malformed response bodies could execute hostile `get()` hooks raising
  `client_secret=oauth-json-body-secret` or `client_secret=oauth-json-dict-secret` before token
  validation failed closed.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_692_documents_servicenow_oauth_body_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added a scoped OAuth response body helper for `OAuthClientCredentials._fetch_token()`.
- ServiceNow OAuth response bodies must be exact dictionaries before `access_token` lookup.
- Mapping-like objects and dict subclasses fail with a fixed `ServiceNowApiError` diagnostic and
  are not stringified or reflected.
- Documented the ServiceNow OAuth body boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "oauth_client_credentials_rejects_json_body_object_without_leak or oauth_client_credentials_rejects_json_body_dict_subclass_without_leak"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_servicenow.py -q -k "oauth_client_credentials_rejects_json_body_object_without_leak or oauth_client_credentials_rejects_json_body_dict_subclass_without_leak"`
  passed, 2 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_692`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_691 or sprint_692"` passed,
  2 tests.
- `python3 -m pytest tests/test_servicenow.py -q -k "oauth_client_credentials_rejects_json_body_object_without_leak or oauth_client_credentials_rejects_json_body_dict_subclass_without_leak or oauth_client_credentials_rejects_response_object_without_leak or oauth_client_credentials_rejects_status_code_object_without_leak or oauth_client_credentials_rejects_status_code_outside_http_range or oauth_client_credentials_raises_when_access_token_is_missing or oauth_client_credentials_reuses_cached_token"`
  passed, 8 tests.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 215 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2946 tests with 93.16% total coverage.
