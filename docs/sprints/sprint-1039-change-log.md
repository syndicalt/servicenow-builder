# Sprint 1039 Change Log - Direct alert webhook URL exact-string guard

## Summary

Sprint 1039 continued production hardening by tightening direct alert webhook URL validation.
Environment-loaded `JEDI_ALERT_WEBHOOK_URL` values were already constrained, but direct
`RuntimeSettings` objects could still carry string subclasses into production startup validation
when `JEDI_ALERT_WEBHOOK_ENABLED=true`.

## Security

- `validate_runtime_settings()` now routes direct `RuntimeSettings.alert_webhook_url` through the
  shared exact-string runtime setting reader before enabled-alert checks.
- String subclasses and non-string objects fail closed with
  `JEDI_ALERT_WEBHOOK_URL must be a string runtime setting`.
- The guard runs before truthiness checks, URL parsing, SSRF validation, sensitive-query validation,
  or production error aggregation.
- Diagnostics name only `JEDI_ALERT_WEBHOOK_URL` and do not echo object type names, object string
  output, URL fragments, host fragments, or credential-like fragments.

## Tests

- Added 1 failing-first direct alert webhook URL string-subclass assertion:
  `test_validate_runtime_settings_rejects_alert_webhook_url_string_subclass_without_leak`.
- Added documentation coverage:
  `test_sprint_1039_documents_direct_alert_webhook_url_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct alert webhook URL validation executed a
  string-subclass truthiness hook before rejecting the malformed value.
- Focused runtime tests passed after implementation.
