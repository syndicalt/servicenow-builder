# Sprint 1033 Change Log - Direct Update Set user exact-string guard

## Summary

Sprint 1033 continued production hardening for legacy local Update Set apply controls by tightening
direct `RuntimeSettings.update_set_user_name` validation. Environment-loaded
`JEDI_UPDATE_SET_USER_NAME` values were already constrained, but direct settings objects could still
reach production startup validation with malformed operator identity values.

## Security

- `validate_runtime_settings()` now routes `RuntimeSettings.update_set_user_name` through the shared
  exact-string runtime setting reader before `JEDI_UPDATE_SET_APPLY=true` operator checks.
- String subclasses and non-string objects fail closed with
  `JEDI_UPDATE_SET_USER_NAME must be a string runtime setting`.
- The guard runs before truthiness checks, control-character scans, or production error aggregation.
- Diagnostics name only `JEDI_UPDATE_SET_USER_NAME` and do not echo object type names, object string
  output, or credential-like fragments.

## Tests

- Added 1 failing-first direct update-set user name string-subclass assertion:
  `test_validate_runtime_settings_rejects_update_set_apply_operator_string_subclass_without_leak`.
- Added documentation coverage:
  `test_sprint_1033_documents_direct_update_set_user_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct update-set user validation executed a
  truthiness hook on a string subclass before rejecting the malformed value.
- Focused runtime tests passed after implementation.
