# Sprint 691 Change Log - ServiceNow OAuth response status boundary

## Scope

Hardened ServiceNow OAuth token acquisition so the OAuth response object and status code are
validated before status comparison or token parsing. This protects the authentication boundary from
alternate transport objects, hostile status-code values, and out-of-range HTTP statuses.

## Tests First

- Added 4 failing-first ServiceNow OAuth response assertions:
  - `tests/test_servicenow.py::test_oauth_client_credentials_rejects_response_object_without_leak`
  - `tests/test_servicenow.py::test_oauth_client_credentials_rejects_status_code_object_without_leak`
  - `tests/test_servicenow.py::test_oauth_client_credentials_rejects_status_code_outside_http_range[99]`
  - `tests/test_servicenow.py::test_oauth_client_credentials_rejects_status_code_outside_http_range[600]`
- Initial failures proved hostile response attribute and comparison hooks could raise
  `client_secret=oauth-response-object-secret` or `client_secret=oauth-status-code-secret`, status
  `99` was accepted, and status `600` used the generic OAuth failure diagnostic.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_691_documents_servicenow_oauth_response_status_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added a scoped OAuth response boundary helper for `OAuthClientCredentials._fetch_token()`.
- ServiceNow OAuth token responses must be exact `HttpResponse` instances before status access.
- OAuth status codes must be exact integers in the HTTP `100..599` range before comparison.
- Malformed OAuth response objects fail with fixed `ServiceNowApiError` diagnostics and are not
  stringified or reflected.
- Documented the ServiceNow OAuth response boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "oauth_client_credentials_rejects_response_object_without_leak or oauth_client_credentials_rejects_status_code_object_without_leak or oauth_client_credentials_rejects_status_code_outside_http_range"`
  failed first with 4 failures.
- `python3 -m pytest tests/test_servicenow.py -q -k "oauth_client_credentials_rejects_response_object_without_leak or oauth_client_credentials_rejects_status_code_object_without_leak or oauth_client_credentials_rejects_status_code_outside_http_range"`
  passed, 4 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_691`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_691` passed, 1 test.
- `python3 -m pytest tests/test_servicenow.py -q -k "oauth_client_credentials_rejects_response_object_without_leak or oauth_client_credentials_rejects_status_code_object_without_leak or oauth_client_credentials_rejects_status_code_outside_http_range or oauth_client_credentials_raises_on_token_failure or oauth_client_credentials_reuses_cached_token"`
  passed, 6 tests.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 213 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2943 tests with 93.16% total coverage.
