# Sprint 824 Change Log - Admin Basic-auth policy parity

## Scope

Centralized admin Basic-auth credential policy so settings loading and request-time Basic-auth parsing share bounded credential handling for the development admin console.

## Tests First

- Added 1 failing-first admin console credential ceiling assertion: `tests/test_runtime.py::test_load_runtime_settings_rejects_oversized_admin_console_credentials`.
- Added 1 failing-first shared Basic-auth policy assertion: `tests/test_runtime.py::test_admin_basic_auth_policy_is_shared_by_startup_and_request_time`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_824_documents_admin_basic_auth_policy_parity`.
- Initial failure proved oversized configured `JEDI_ADMIN_CONSOLE_USERNAME` and `JEDI_ADMIN_CONSOLE_PASSWORD` values were accepted during settings loading, and no shared `MAX_BASIC_AUTH_CREDENTIAL_BYTES` policy module existed.

## Changes

- Added `jedi_devproject.admin_basic_auth_policy` as the shared source for Basic-auth encoded byte ceiling and decoded credential-part byte ceiling.
- Runtime settings loading now rejects configured admin console username or password values larger than 8192 bytes before the API starts.
- Runtime request auth delegates decoded Basic-auth username/password validation to the shared credential policy.
- Updated the operator guide to document that settings loading and request-time Basic-auth parsing share bounded credential policy.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "oversized_admin_console_credentials or admin_basic_auth_policy_is_shared or malformed_configured_credentials_before_decode or basic_auth"` - 23 passed, 351 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_824 or sprint_823"` - 2 passed, 895 deselected.
- `python3 -m pytest tests/test_runtime.py -q` - 374 passed.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 201 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3250 passed, 93.42% coverage.
