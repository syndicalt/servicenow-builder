# Sprint 1030 Change Log - Direct model setting exact-string guard

## Summary

Sprint 1030 continued production hardening by tightening direct `RuntimeSettings` model-provider
validation. Environment-loaded model settings were already exact-string guarded, but direct settings
objects could still reach `validate_runtime_settings()` with malformed `model_provider`,
`openai_api_key`, or `openai_model` values created through in-process construction or unchecked model
copies.

## Security

- `validate_runtime_settings()` now routes `RuntimeSettings.model_provider` through the direct
  optional exact-string reader before `len()`, provider equality checks, unsupported-provider
  diagnostics, or worker model routing.
- `validate_runtime_settings()` now routes `RuntimeSettings.openai_api_key` and
  `RuntimeSettings.openai_model` through the direct optional exact-string reader before truthiness
  checks, OpenAI-required-field checks, or whitespace/control-character scans.
- String subclasses and non-string objects fail closed with `<SETTING> must be a string runtime
  setting`.
- Diagnostics name only `JEDI_MODEL_PROVIDER`, `OPENAI_API_KEY`, or `OPENAI_MODEL` and do not echo
  object type names, object string output, or credential-like fragments.

## Tests

- Added 1 failing-first direct model provider string-subclass assertion:
  `test_validate_runtime_settings_rejects_model_provider_string_subclass_without_len_leak`.
- Added 1 failing-first direct OpenAI API key string-subclass assertion:
  `test_validate_runtime_settings_rejects_openai_api_key_string_subclass_without_truthiness_leak`.
- Added documentation coverage:
  `test_sprint_1030_documents_direct_model_setting_exact_string_guard`.

## Verification

- Focused tests failed before implementation because direct model setting validation executed `len()`
  or truthiness on string subclasses before rejecting malformed values.
- Focused runtime tests passed after implementation.
