# Sprint 1037 Change Log - Direct boolean runtime exact-type guard

## Summary

Sprint 1037 continued production hardening by tightening direct boolean runtime setting validation.
Environment-loaded boolean values were already parsed from strict string values, but direct
`RuntimeSettings` objects could still carry truthy or falsey objects into production startup
validation.

## Security

- `validate_runtime_settings()` now routes production boolean controls through a shared exact-boolean
  runtime setting reader before policy checks.
- Truthy or falsey objects, integers, strings, and non-boolean values fail closed with
  `<SETTING> must be a boolean runtime setting`.
- The guard runs before `__bool__` execution, role-policy checks, fail-closed classifier validation,
  HSTS enforcement, build-claim application, legacy Update Set apply checks, alert webhook checks, or
  production error aggregation.
- The protected settings are `JEDI_ALLOW_COMBINED_PRODUCTION`, `JEDI_BUILD_CLAIM_APPLY`,
  `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED`, `JEDI_ALERT_WEBHOOK_ENABLED`,
  `JEDI_UPDATE_SET_APPLY`, and `JEDI_CLASSIFIER_GATE`.
- Diagnostics name only the setting and do not echo object type names, object string output, or
  credential-like fragments.

## Tests

- Added 1 failing-first direct boolean setting object assertion:
  `test_validate_runtime_settings_rejects_boolean_setting_object_without_leak`.
- Added documentation coverage:
  `test_sprint_1037_documents_direct_boolean_runtime_exact_type_guard`.

## Verification

- Focused tests failed before implementation because direct classifier-gate validation executed an
  object `__bool__` hook before rejecting the malformed value.
- Focused runtime tests passed after implementation.
