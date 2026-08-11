# Sprint 554 Change Log

## ServiceNow OAuth access-token size and ASCII guard

Sprint 554 continued production hardening by bounding ServiceNow OAuth access-token response values before they are cached or used to construct outbound `Bearer` credentials. `OAuthClientCredentials._fetch_token()` already rejected missing, empty, padded, whitespace-bearing, and control-character-bearing `access_token` values, but it still accepted non-ASCII and oversized token strings from an alternate transport or malformed OAuth response.

OAuth access-token parsing now rejects non-ASCII values and values larger than 8192 ASCII bytes before caching the token or building an Authorization header. Oversized and malformed token responses fail with the fixed `ServiceNow OAuth response did not include access_token` diagnostic. The diagnostic does not echo token values, token fragments, object representations, or credential-like payloads.

This keeps a malformed OAuth response from creating an oversized outbound header, retaining unbounded credential material in memory, or passing non-ASCII credential bytes into HTTP header construction.

Verification:

- Added 1 failing-first ServiceNow OAuth oversized access-token test proving an 8193-byte token response is rejected before it can be cached or returned as a `Bearer` header.
- Extended malformed access-token coverage to reject non-ASCII token values.
- `python3 -m pytest tests/test_servicenow.py::test_oauth_client_credentials_rejects_oversized_access_token_without_caching -q`: failed before implementation because the oversized token was accepted.
- `python3 -m pytest tests/test_servicenow.py::test_oauth_client_credentials_requests_token_without_logging_secret tests/test_servicenow.py::test_oauth_client_credentials_reuses_cached_token tests/test_servicenow.py::test_oauth_client_credentials_raises_when_access_token_is_missing tests/test_servicenow.py::test_oauth_client_credentials_rejects_malformed_access_token tests/test_servicenow.py::test_oauth_client_credentials_rejects_oversized_access_token_without_caching -q`: 8 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 156 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 628 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2579 tests passed; required 90% coverage reached with 93.41% total coverage.
