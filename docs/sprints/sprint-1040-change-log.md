# Sprint 1040 Change Log - Direct audit root exact-path guard

## Summary

Sprint 1040 continued production hardening by tightening direct audit-root validation. Load-time
`JEDI_AUDIT_ROOT` values were already exact-string guarded before `Path(...)` construction, but
direct `RuntimeSettings.audit_root` values could still carry arbitrary objects into production
startup validation.

## Security

- `_audit_root_errors()` now routes direct `RuntimeSettings.audit_root` through a shared exact
  concrete-path runtime setting reader before audit-root hygiene checks.
- Non-path objects and path subclasses fail closed with
  `JEDI_AUDIT_ROOT must be a path runtime setting`.
- The guard runs before `str()`, `is_absolute()`, whitespace/control-character scans, or production
  error aggregation.
- Diagnostics name only `JEDI_AUDIT_ROOT` and do not echo object type names, object string output,
  filesystem path fragments, or credential-like fragments.

## Tests

- Added 1 failing-first direct audit-root object assertion:
  `test_validate_runtime_settings_rejects_direct_audit_root_object_without_leak`.
- Added documentation coverage:
  `test_sprint_1040_documents_direct_audit_root_exact_path_guard`.

## Verification

- Focused tests failed before implementation because direct audit-root validation executed an object
  `__str__` hook before rejecting the malformed value.
- Focused runtime tests passed after implementation.
