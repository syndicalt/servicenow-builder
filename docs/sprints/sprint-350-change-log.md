# Sprint 350 Change Log

Scope: Production hardening - ServiceNow OAuth access-token response normalization.

## Summary

- ServiceNow OAuth token extraction now rejects malformed `access_token` response values before caching or Authorization header construction.
- Missing, empty, padded, whitespace-bearing, and control-character-bearing access tokens fail with the existing fixed OAuth response diagnostic.
- OAuth token response material is no longer trimmed or accepted as a bearer credential when malformed.
- Valid token responses and cached-token reuse behavior remain unchanged.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_oauth_client_credentials_rejects_malformed_access_token -q` - 3 tests failed before implementation because padded and control-character-bearing access tokens were accepted.
- `python3 -m pytest tests/test_servicenow.py -q -k "oauth_client_credentials"` - 7 passed after implementation.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_fifty_documents_servicenow_oauth_token_no_trim -q` - 1 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 424 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 2021 passed, total coverage 94.07%.
