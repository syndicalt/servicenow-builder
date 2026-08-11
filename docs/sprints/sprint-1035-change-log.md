# Sprint 1035 Change Log - Direct integer runtime exact-type guard

## Summary

Sprint 1035 continued production hardening by tightening direct integer runtime setting validation.
Environment-loaded numeric values were already parsed from ASCII decimal strings, but direct
`RuntimeSettings` objects could still carry int subclasses or non-integer objects into production
startup validation.

## Security

- `validate_runtime_settings()` now routes production integer settings through a shared exact-integer
  runtime setting reader before positive-value and maximum checks.
- Int subclasses, booleans, floats, strings, and non-integer objects fail closed with
  `<SETTING> must be an integer runtime setting`.
- The guard runs before comparison operators, positive-value checks, maximum caps, or production
  error aggregation.
- The protected settings include lifecycle webhook body and skew limits, lifecycle and admin rate
  limits, admin body limits, HSTS max-age, stale-job requeue windows, alert webhook body limits, and
  public-web size and result limits.
- Diagnostics name only the setting and do not echo object type names, object string output, or
  credential-like fragments.

## Tests

- Added 1 failing-first direct positive integer setting subclass assertion:
  `test_validate_runtime_settings_rejects_positive_int_setting_subclass_without_leak`.
- Added documentation coverage:
  `test_sprint_1035_documents_direct_integer_runtime_exact_type_guard`.

## Verification

- Focused tests failed before implementation because direct positive integer validation executed an
  int-subclass comparison hook before rejecting the malformed value.
- Focused runtime tests passed after implementation.
