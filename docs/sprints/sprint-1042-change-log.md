# Sprint 1042 Change Log - Direct ServiceNow instance URL exact-string guard

## Summary

Sprint 1042 continued production hardening by tightening direct ServiceNow instance URL validation. Load-time `SERVICENOW_INSTANCE_URL`, `SERVICENOW_PM_INSTANCE_URL`, and `SERVICENOW_DEV_INSTANCE_URL` values were already exact-string guarded, but direct `RuntimeSettings` values could still carry string subclasses into production startup validation.

## Security

- `_servicenow_instance_url_errors()` now routes direct ServiceNow instance URLs through the shared exact-string runtime setting reader before URL hygiene checks.
- String subclasses and non-string objects fail closed with `<SETTING> must be a string runtime setting`.
- The guard runs before URL parsing, whitespace/control-character scans, encoded-control scans, HTTPS checks, credential checks, fragment checks, hostname checks, or production error aggregation.
- Diagnostics name only the ServiceNow URL setting and do not echo object type names, object string output, credential fragments, host fragments, or URL fragments.

## Tests

- Added 1 failing-first direct ServiceNow instance URL string-subclass assertion: `test_validate_runtime_settings_rejects_servicenow_instance_url_string_subclass_without_leak`.
- Added documentation coverage: `test_sprint_1042_documents_direct_servicenow_url_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct ServiceNow URL validation reached lower-level URL safety validation before producing a setting-name `RuntimeConfigError`.
- Focused runtime tests passed after implementation.
