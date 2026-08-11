# Sprint 1029 Change Log - Direct auth mode exact-string guard

## Summary

Sprint 1029 continued production hardening by tightening direct `RuntimeSettings` auth-mode
validation. Environment-loaded auth modes were already exact-string guarded, but direct settings
objects could still reach `validate_runtime_settings()` with malformed `lifecycle_webhook_auth_mode`
or `admin_auth_mode` values created through in-process construction or unchecked model copies.

## Security

- `validate_runtime_settings()` now routes `RuntimeSettings.lifecycle_webhook_auth_mode` through the
  shared exact-string runtime setting reader before production webhook-auth equality checks.
- `validate_runtime_settings()` now routes `RuntimeSettings.admin_auth_mode` through the shared
  exact-string runtime setting reader before `str()` conversion, whitespace/control-character scans,
  allowed-mode checks, admin-auth requirement checks, or unimplemented-auth diagnostics.
- String subclasses and non-string objects fail closed with `<SETTING> must be a string runtime
  setting`.
- Diagnostics name only `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE` or `JEDI_ADMIN_AUTH_MODE` and do not echo
  object type names, object string output, or credential-like fragments.

## Tests

- Added 1 failing-first direct lifecycle webhook auth mode string-subclass assertion:
  `test_validate_runtime_settings_rejects_lifecycle_auth_mode_string_subclass_without_eq_leak`.
- Added 1 failing-first direct admin auth mode non-string assertion:
  `test_validate_runtime_settings_rejects_admin_auth_mode_non_string_without_str_leak`.
- Added documentation coverage:
  `test_sprint_1029_documents_direct_auth_mode_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct auth-mode validation executed `!=` on a
  string subclass and `str()` on a non-string admin auth mode before rejecting malformed values.
- Focused runtime tests passed after implementation.
