# Sprint 1028 Change Log - Direct production credential exact-string guard

## Summary

Sprint 1028 continued production hardening by tightening direct `RuntimeSettings` credential
validation. Environment-loaded credentials were already exact-string guarded, but direct settings
objects could still reach `validate_runtime_settings()` with malformed `lifecycle_webhook_secret` or
`admin_api_token` values created through in-process construction or unchecked model copies.

## Security

- Added `_direct_optional_runtime_setting_text()` for direct optional runtime setting validation.
- `validate_runtime_settings()` now routes `RuntimeSettings.lifecycle_webhook_secret` through this
  exact-string guard before truthiness checks, `len()`, lifecycle webhook credential byte-length
  checks, whitespace/control-character scans, or production webhook-auth validation.
- `validate_runtime_settings()` now routes `RuntimeSettings.admin_api_token` through this
  exact-string guard before `len()`, admin bearer token byte-length checks, ASCII checks,
  whitespace/control-character scans, admin-auth requirement checks, or production error aggregation.
- String subclasses and non-string objects fail closed with `<SETTING> must be a string runtime
  setting`.
- Diagnostics name only `JEDI_LIFECYCLE_WEBHOOK_SECRET` or `JEDI_ADMIN_API_TOKEN` and do not echo
  object type names, object string output, or credential-like fragments.

## Tests

- Added 1 failing-first direct lifecycle webhook secret string-subclass assertion:
  `test_validate_runtime_settings_rejects_webhook_secret_string_subclass_without_len_leak`.
- Added 1 failing-first direct admin API token string-subclass assertion:
  `test_validate_runtime_settings_rejects_admin_api_token_string_subclass_without_len_leak`.
- Added documentation coverage:
  `test_sprint_1028_documents_direct_production_credential_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct production credential validation executed
  truthiness or `len()` on string subclasses before rejecting malformed values.
- Focused runtime tests passed after implementation.
