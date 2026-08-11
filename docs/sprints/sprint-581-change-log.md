# Sprint 581 Change Log

## ServiceNow OAuth access-token string-subclass guard

Sprint 581 continued production hardening by preventing ServiceNow OAuth access-token validation from dispatching string methods on hostile string subclasses. `OAuthClientCredentials._fetch_token()` already rejected missing, empty, non-ASCII, oversized, padded, whitespace-bearing, and control-character-bearing `access_token` response values before caching or returning a `Bearer` credential, but it still accepted `str` subclasses and called `strip()` before returning the fixed `ServiceNow OAuth response did not include access_token` diagnostic.

OAuth access-token validation now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow OAuth response did not include access_token` diagnostic before ASCII checks, byte-length calculation, trim checks, whitespace/control-character scans, token caching, `Bearer` Authorization header construction, or credential return. This preserves normal OAuth behavior while preventing alternate transports, tests, or malformed OAuth responses from surfacing custom exception text, object representations, or credential-like payloads through token string methods.

This keeps malformed OAuth responses from becoming cached credentials or producing unbounded or attacker-controlled outbound Authorization headers.

Verification:

- Added 1 failing-first ServiceNow OAuth access-token string-subclass test proving a hostile `str` subclass raised `RuntimeError` from overridden `strip()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_oauth_client_credentials_rejects_access_token_str_subclass_without_caching -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from overridden `strip()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_oauth_client_credentials_rejects_access_token_str_subclass_without_caching tests/test_servicenow.py::test_oauth_client_credentials_rejects_malformed_access_token tests/test_servicenow.py::test_oauth_client_credentials_rejects_oversized_access_token_without_caching tests/test_servicenow.py::test_oauth_client_credentials_raises_when_access_token_is_missing tests/test_servicenow.py::test_oauth_client_credentials_reuses_cached_token -q`: 8 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_581_documents_servicenow_oauth_access_token_str_subclass_guard -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 183 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 655 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2633 passed, 93.39% coverage.
