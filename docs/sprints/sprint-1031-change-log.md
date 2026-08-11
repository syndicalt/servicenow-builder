# Sprint 1031 Change Log - Direct public web access exact-string guard

## Summary

Sprint 1031 continued production hardening by tightening direct `RuntimeSettings` public-web access
validation. Environment-loaded public-web access values were already exact-string guarded, but direct
settings objects could still reach `validate_runtime_settings()` with malformed
`public_web_access` values created through in-process construction or unchecked model copies.

## Security

- `validate_runtime_settings()` now routes `RuntimeSettings.public_web_access` through the shared
  exact-string runtime setting reader before production public-web equality checks.
- API-role worker-only checks and production public documentation allowlist checks now use the
  guarded `JEDI_PUBLIC_WEB_ACCESS` value.
- String subclasses and non-string objects fail closed with
  `JEDI_PUBLIC_WEB_ACCESS must be a string runtime setting`.
- Diagnostics name only `JEDI_PUBLIC_WEB_ACCESS` and do not echo object type names, object string
  output, or credential-like fragments.

## Tests

- Added 1 failing-first direct public-web access string-subclass assertion:
  `test_validate_runtime_settings_rejects_public_web_access_string_subclass_without_eq_leak`.
- Added documentation coverage:
  `test_sprint_1031_documents_direct_public_web_access_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct public-web access validation executed an
  equality hook on a string subclass before rejecting the malformed value.
- Focused runtime tests passed after implementation.
