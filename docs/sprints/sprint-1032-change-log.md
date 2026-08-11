# Sprint 1032 Change Log - Direct worker id exact-string guard

## Summary

Sprint 1032 continued production hardening by tightening direct `RuntimeSettings.worker_id`
validation. Environment-loaded worker ids were already guarded, but direct settings objects could
still reach `validate_runtime_settings()` with malformed `worker_id` values created through
in-process construction or unchecked model copies.

## Security

- `validate_runtime_settings()` now routes `RuntimeSettings.worker_id` through the shared
  exact-string runtime setting reader before production worker-id hygiene checks.
- String subclasses and non-string objects fail closed with
  `JEDI_WORKER_ID must be a string runtime setting`.
- The guard runs before truthiness checks, `.strip()`, control-character scans, or production error
  aggregation.
- Diagnostics name only `JEDI_WORKER_ID` and do not echo object type names, object string output, or
  credential-like fragments.

## Tests

- Added 1 failing-first direct worker id string-subclass assertion:
  `test_validate_runtime_settings_rejects_worker_id_string_subclass_without_truthiness_leak`.
- Added documentation coverage:
  `test_sprint_1032_documents_direct_worker_id_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct worker id validation executed a
  truthiness hook on a string subclass before rejecting the malformed value.
- Focused runtime tests passed after implementation.
