# Sprint 810 Change Log - Production admin console credential rejection

## Scope

Hardened public production auth configuration so development-only Basic-auth console credentials
cannot be deployed beside the supported bearer-token admin API posture.

## Tests First

- Added 2 failing-first public production credential assertions:
  `tests/test_runtime.py::test_validate_runtime_settings_rejects_admin_console_credentials_on_public_production_roles`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_810_documents_production_admin_console_credential_rejection`.
- Initial failures proved `JEDI_RUNTIME_ROLE=api` and `JEDI_RUNTIME_ROLE=combined` accepted
  `JEDI_ADMIN_CONSOLE_USERNAME` and `JEDI_ADMIN_CONSOLE_PASSWORD` in production when bearer-token
  admin access was configured.

## Changes

- `validate_runtime_settings()` now rejects `JEDI_ADMIN_CONSOLE_USERNAME` and
  `JEDI_ADMIN_CONSOLE_PASSWORD` on public production roles.
- `JEDI_ADMIN_AUTH_MODE=disabled` with a strong `JEDI_ADMIN_API_TOKEN` remains the supported
  interim production posture.
- Development Basic-auth console credentials remain available only outside production.
- Updated the operator guide to document the dev-only credential boundary.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "admin_console_credentials_on_public_production_roles or allows_production_api_with_admin_console_disabled_and_token"`: 3 passed, 357 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_810`: 1 passed, 882 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 360 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3217 passed, 93.37% coverage.
