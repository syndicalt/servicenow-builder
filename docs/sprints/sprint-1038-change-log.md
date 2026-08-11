# Sprint 1038 Change Log - Direct build-claim state exact-string guard

## Summary

Sprint 1038 continued production hardening by tightening direct build-claim state validation.
Environment-loaded `JEDI_BUILD_CLAIM_FROM_STATE` and `JEDI_BUILD_CLAIM_STATE` values were already
constrained, but direct `RuntimeSettings` objects could still carry string subclasses into
production startup validation when `JEDI_BUILD_CLAIM_APPLY=true`.

## Security

- `_build_claim_state_errors()` now routes both direct build-claim state values through the shared
  exact-string runtime setting reader before hygiene checks.
- String subclasses and non-string objects fail closed with
  `JEDI_BUILD_CLAIM_FROM_STATE must be a string runtime setting` or
  `JEDI_BUILD_CLAIM_STATE must be a string runtime setting`.
- The guard runs before truthiness checks, `.strip()`, control-character scans, or production error
  aggregation.
- Diagnostics name only the setting and do not echo object type names, object string output, or
  credential-like fragments.

## Tests

- Added 1 failing-first direct build-claim state string-subclass assertion:
  `test_validate_runtime_settings_rejects_build_claim_state_string_subclass_without_leak`.
- Added documentation coverage:
  `test_sprint_1038_documents_direct_build_claim_state_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct build-claim state validation executed a
  string-subclass truthiness hook before rejecting the malformed value.
- Focused runtime tests passed after implementation.
