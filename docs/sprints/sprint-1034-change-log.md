# Sprint 1034 Change Log - Direct public-web list exact-string guard

## Summary

Sprint 1034 continued production hardening for worker public-documentation retrieval by tightening
direct `RuntimeSettings.public_web_allowed_domains` and `RuntimeSettings.public_web_doc_urls`
validation. Environment-loaded CSV values were already parsed into string lists, but direct settings
objects could still carry malformed containers or string subclasses into production startup
validation.

## Security

- `validate_runtime_settings()` now routes direct public-web allowlist and documentation URL
  collections through an exact list-of-exact-strings reader before outbound retrieval validation.
- Non-list containers, string subclasses, and non-string entries fail closed with
  `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS must be a string list setting` or
  `JEDI_PUBLIC_WEB_DOC_URLS must be a string list setting`.
- The guard runs before truthiness checks, hostname normalization, `.strip()`, URL parsing,
  allowlist matching, or production error aggregation.
- Diagnostics name only the public-web setting and do not echo object type names, object string
  output, URL fragments, host fragments, or credential-like fragments.

## Tests

- Added 1 failing-first direct public-web allowed-domain string-subclass assertion:
  `test_validate_runtime_settings_rejects_public_web_allowed_domains_string_subclass_without_leak`.
- Added documentation coverage:
  `test_sprint_1034_documents_direct_public_web_list_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct public-web allowlist validation executed
  a string-subclass `.strip()` hook before rejecting the malformed value.
- Focused runtime tests passed after implementation.
