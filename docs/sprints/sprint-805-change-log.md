# Sprint 805 Change Log - Production admin disabled-with-bearer posture

## Scope

Made the production API startable with an implemented interim admin posture: browser admin disabled,
JSON diagnostics protected by a strong bearer token.

## Tests First

- Added 3 failing-first production admin posture assertions in `tests/test_runtime.py`:
  - `test_validate_runtime_settings_rejects_production_without_admin_api_token_or_auth`
  - `test_validate_runtime_settings_allows_production_api_with_admin_console_disabled_and_token`
  - `test_create_runtime_api_allows_production_with_disabled_console_and_admin_token`
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_805_documents_production_admin_disabled_with_bearer_posture`.
- Initial failures proved production API validation rejected `JEDI_ADMIN_AUTH_MODE=disabled` even
  when `JEDI_ADMIN_API_TOKEN` was configured, leaving no implemented production admin posture.

## Changes

- `validate_runtime_settings()` now permits `JEDI_ADMIN_AUTH_MODE=disabled` for public production
  runtime roles only when `JEDI_ADMIN_API_TOKEN` is configured.
- Production validation still rejects missing, short, padded, whitespace-bearing, or
  control-character-bearing `JEDI_ADMIN_API_TOKEN` values.
- Browser admin console routes remain fail-closed with `503` when admin auth mode is disabled.
- JSON admin diagnostics and artifact APIs remain protected by `Authorization: Bearer
  <JEDI_ADMIN_API_TOKEN>`.
- `dev_basic` remains development-only, and reserved `oidc` and `servicenow_oauth` modes remain
  fail-closed until implemented.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "production_without_admin_api_token_or_auth or production_api_with_admin_console_disabled_and_token or production_with_disabled_console_and_admin_token"`: 3 passed, 349 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 352 passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_805`: 1 passed, 877 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3204 passed, 93.36% coverage.
