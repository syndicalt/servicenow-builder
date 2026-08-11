# Sprint 1044 Change Log - Direct admin console credential exact-string guard

## Summary

Sprint 1044 continued production hardening by tightening direct admin console credential validation. Load-time `JEDI_ADMIN_CONSOLE_USERNAME` and `JEDI_ADMIN_CONSOLE_PASSWORD` values were already bounded and exact-string validated, but direct `RuntimeSettings` values could still carry string subclasses into production startup validation and reach role-policy rejection before the runtime proved the credential object type.

## Security

- `validate_runtime_settings()` now routes direct admin console username and password values through the shared optional exact-string runtime setting reader before production role-policy checks.
- String subclasses and non-string objects fail closed with `<SETTING> must be a string runtime setting`.
- The guard runs before development-only production rejection, worker/api role checks, truthiness checks, or credential comparison setup.
- Diagnostics name only the admin console setting and do not echo object type names, object string output, credential fragments, or hostile exception text.

## Tests

- Added 1 failing-first direct admin console credential string-subclass assertion: `test_validate_runtime_settings_rejects_admin_console_password_string_subclass_without_leak`.
- Added documentation coverage: `test_sprint_1044_documents_direct_admin_console_credential_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct admin console credential validation reported the production development-only policy before producing a setting-name `RuntimeConfigError`.
- Focused runtime tests passed after implementation.
