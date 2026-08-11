# Sprint 1041 Change Log - Direct database URL exact-string guard

## Summary

Sprint 1041 continued production hardening by tightening direct database URL validation. Load-time
`DATABASE_URL` values were already exact-string guarded, but direct `RuntimeSettings.database_url`
values could still carry string subclasses into production startup validation.

## Security

- `_database_url_errors()` now routes direct `RuntimeSettings.database_url` through the shared
  exact-string runtime setting reader before database URL hygiene checks.
- String subclasses and non-string objects fail closed with
  `DATABASE_URL must be a string runtime setting`.
- The guard runs before URL parsing, whitespace/control-character scans, encoded-control scans,
  scheme checks, fragment checks, hostname checks, or production error aggregation.
- Diagnostics name only `DATABASE_URL` and do not echo object type names, object string output,
  database credential fragments, host fragments, or URL fragments.

## Tests

- Added 1 failing-first direct database URL string-subclass assertion:
  `test_validate_runtime_settings_rejects_database_url_string_subclass_without_leak`.
- Added documentation coverage:
  `test_sprint_1041_documents_direct_database_url_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct database URL validation reached a
  lower-level exact-string validator and raised a raw `ValueError` instead of a setting-name
  `RuntimeConfigError`.
- Focused runtime tests passed after implementation.
