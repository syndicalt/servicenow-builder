# Sprint 1045 Change Log - Runtime role helper normalized-input boundary

## Summary

Sprint 1045 continued production hardening by removing raw `RuntimeSettings` reads from production runtime role-policy helpers where `validate_runtime_settings()` already computes exact-type normalized values. The API-role and worker-role helpers now receive only the normalized provider, webhook, admin, public-web, build-claim, update-set, and admin-console values they need for role-policy decisions.

## Security

- `_api_runtime_role_errors()` no longer reads raw `settings.model_provider`, `settings.openai_api_key`, or `settings.openai_model`.
- `_worker_runtime_role_errors()` no longer reads raw `settings.lifecycle_webhook_auth_mode`, `settings.lifecycle_webhook_secret`, `settings.admin_api_token`, `settings.admin_auth_mode`, `settings.admin_console_username`, or `settings.admin_console_password`.
- Role-policy decisions now stay downstream of the shared exact-string, exact-boolean, and exact-integer runtime setting boundaries.
- This reduces future regression risk where a new role check could accidentally bypass direct-object hardening and inspect a malformed `RuntimeSettings` value directly.

## Tests

- Added 1 failing-first structural role-helper assertion: `test_runtime_role_helpers_do_not_read_raw_settings_for_normalized_fields`.
- Re-ran focused API-role, worker-role, and admin-console production role-policy tests after the refactor.
- Added documentation coverage: `test_sprint_1045_documents_runtime_role_helper_normalized_input_boundary`.

## Verification

- Focused structural tests failed before implementation because the role helpers still read raw normalized-field attributes from `RuntimeSettings`.
- Focused structural and behavior tests passed after implementation.
