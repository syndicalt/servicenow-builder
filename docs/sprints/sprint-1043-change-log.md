# Sprint 1043 Change Log - Direct ServiceNow OAuth credential exact-string guard

## Summary

Sprint 1043 continued production hardening by tightening direct ServiceNow OAuth credential validation. Load-time `SERVICENOW_CLIENT_ID`, `SERVICENOW_CLIENT_SECRET`, `SERVICENOW_PM_CLIENT_ID`, `SERVICENOW_PM_CLIENT_SECRET`, `SERVICENOW_DEV_CLIENT_ID`, and `SERVICENOW_DEV_CLIENT_SECRET` values were already exact-string guarded, but direct `RuntimeSettings` values could still carry string subclasses into production startup validation.

## Security

- `_servicenow_oauth_credential_errors()` now routes direct ServiceNow OAuth credential values through the shared exact-string runtime setting reader before credential hygiene checks.
- String subclasses and non-string objects fail closed with `<SETTING> must be a string runtime setting`.
- The guard runs before truthiness checks, padding checks, whitespace/control-character scans, or production error aggregation.
- Diagnostics name only the ServiceNow OAuth setting and do not echo object type names, object string output, credential fragments, or hostile exception text.

## Tests

- Added 1 failing-first direct ServiceNow OAuth credential string-subclass assertion: `test_validate_runtime_settings_rejects_servicenow_oauth_secret_string_subclass_without_leak`.
- Added documentation coverage: `test_sprint_1043_documents_direct_servicenow_oauth_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct ServiceNow OAuth credential validation executed string-subclass truthiness behavior before producing a setting-name `RuntimeConfigError`.
- Focused runtime tests passed after implementation.
