# Sprint 1036 Change Log - Direct timeout finite-number guard

## Summary

Sprint 1036 continued production hardening by tightening direct outbound timeout validation.
Environment-loaded timeout values were already parsed as finite ASCII decimal numbers, but direct
`RuntimeSettings` objects could still carry float subclasses or non-finite values into production
startup validation.

## Security

- `validate_runtime_settings()` now routes direct outbound timeout settings through a shared exact
  finite-number runtime setting reader before positive-value and maximum checks.
- Float subclasses, booleans, strings, non-finite floats, and non-number objects fail closed with
  `<SETTING> must be a finite number runtime setting`.
- The guard runs before comparison operators, positive-value checks, maximum caps, or production
  error aggregation.
- The protected settings are `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS` and
  `JEDI_PUBLIC_WEB_TIMEOUT_SECONDS`.
- Diagnostics name only the setting and do not echo object type names, object string output, or
  credential-like fragments.

## Tests

- Added 1 failing-first direct timeout setting subclass assertion:
  `test_validate_runtime_settings_rejects_timeout_setting_subclass_without_leak`.
- Added documentation coverage:
  `test_sprint_1036_documents_direct_timeout_finite_number_guard`.

## Verification

- Focused tests failed before implementation because direct timeout validation executed a
  float-subclass comparison hook before rejecting the malformed value.
- Focused runtime tests passed after implementation.
