# Sprint 823 Change Log - Admin bearer token policy parity

## Scope

Centralized admin bearer token policy so production startup validation and request-time admin authentication cannot drift on the configured bearer-token byte ceiling.

## Tests First

- Added 1 failing-first shared admin bearer token policy assertion: `tests/test_runtime.py::test_admin_bearer_token_limit_policy_is_shared_by_startup_and_request_time`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_823_documents_admin_bearer_token_policy_parity`.
- Initial failure proved there was no shared `MAX_ADMIN_BEARER_TOKEN_BYTES` policy module for startup validation and request-time auth.

## Changes

- Added `jedi_devproject.admin_token_policy` as the shared source for admin bearer token byte ceiling and malformed-token detection.
- Runtime startup validation now imports the same `MAX_ADMIN_BEARER_TOKEN_BYTES` value as request-time bearer auth.
- Runtime request auth delegates configured and inbound bearer-token malformed checks to the shared policy.
- Updated the operator guide to document that startup validation and request-time auth share one bearer token ceiling.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "admin_bearer_token_limit_policy_is_shared or malformed_configured_token or non_ascii_admin_api_token or oversized_admin_api_token"` - 7 passed, 364 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_823 or sprint_822 or sprint_821"` - 3 passed, 893 deselected.
- `python3 -m pytest tests/test_runtime.py -q` - 371 passed.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 200 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3246 passed, 93.41% coverage.
