# Sprint 1027 Change Log - Direct runtime mode exact-string guard

## Summary

Sprint 1027 continued production hardening by tightening direct `RuntimeSettings` validation.
Environment-loaded settings were already exact-string guarded, but direct settings objects could
still reach `validate_runtime_settings()` with malformed `runtime_environment` or `runtime_role`
values created through in-process construction or unchecked model copies.

## Security

- `_runtime_environment()` now routes `RuntimeSettings.runtime_environment` through the shared
  exact-string runtime setting reader before `.strip()`, whitespace checks, lowercasing, or
  production/development branching.
- `_runtime_role()` now routes `RuntimeSettings.runtime_role` through the shared exact-string
  runtime setting reader before `str()` conversion, `.strip()`, enum checks, runtime role routing, or
  role-specific production checks.
- String subclasses and non-string objects fail closed with `<SETTING> must be a string runtime
  setting`.
- Diagnostics name only `JEDI_ENVIRONMENT` or `JEDI_RUNTIME_ROLE` and do not echo object type names,
  object string output, or credential-like fragments.

## Tests

- Added 1 failing-first direct runtime environment string-subclass assertion:
  `test_validate_runtime_settings_rejects_runtime_environment_string_subclass_without_method_leak`.
- Added 1 failing-first direct runtime role non-string assertion:
  `test_validate_runtime_settings_rejects_runtime_role_non_string_without_str_leak`.
- Added documentation coverage:
  `test_sprint_1027_documents_direct_runtime_mode_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct runtime validation executed `.strip()` on
  a string subclass and `str()` on a non-string runtime role.
- Focused runtime tests passed after implementation.
