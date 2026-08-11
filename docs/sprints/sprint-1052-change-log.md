# Sprint 1052 Change Log - Runtime auth configured settings boundary

## Summary

Sprint 1052 continued production hardening by tightening request-time admin authentication around configured `RuntimeSettings` values. Startup validation already exact-string guards admin API tokens and local development console credentials, but request-time auth still read configured token, auth mode, runtime environment, username, and password values directly before bearer-token comparison or Basic-auth parsing. Embedded callers using mutated settings objects could therefore execute string-subclass truthiness, length, or equality hooks while authenticating admin operators.

Request-time admin auth now normalizes configured auth settings before decoding credentials, checking auth modes, evaluating configured credential presence, or calling constant-time comparisons. Malformed direct settings fail closed as `HTTPException` 503 responses with fixed diagnostics and no exception cause.

## Changes

- `_require_admin_token()` now exact-string validates `RuntimeSettings.admin_api_token` before truthiness, bearer-token policy checks, or constant-time comparison.
- `_require_admin_console_credentials()` now exact-string validates `RuntimeSettings.admin_auth_mode`, `RuntimeSettings.runtime_environment`, `RuntimeSettings.admin_console_username`, and `RuntimeSettings.admin_console_password` before auth-mode equality checks, Basic-auth decoding, configured credential truthiness checks, or username/password comparison.
- Added request-time helpers that map malformed configured auth settings to fixed fail-closed admin diagnostics.
- Updated the operator guide to document request-time configured admin-auth validation.

## Tests

- Added 3 failing-first request-time admin auth boundary assertions:
  - `test_admin_console_rejects_auth_mode_subclass_before_equality`
  - `test_admin_console_rejects_password_subclass_before_compare`
  - `test_admin_bearer_token_rejects_configured_token_subclass_before_compare`
- Initial focused run failed before implementation because request-time auth executed string-subclass `__eq__` or `__len__` hooks.
- Focused regression after implementation:
  - `pytest tests/test_runtime.py -q -k "admin_console_rejects_auth_mode_subclass or admin_console_rejects_password_subclass or admin_bearer_token_rejects_configured_token_subclass"` - 3 passed.
