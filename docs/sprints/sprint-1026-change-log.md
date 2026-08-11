# Sprint 1026 Change Log - Runtime optional setting exact-string guard

## Summary

Sprint 1026 continued production hardening by tightening optional runtime configuration helpers.
Several optional settings called `.strip()`, equality checks, URL validation, provider validation,
or admin credential byte-length checks before proving the configured value was an exact string.
Malformed in-process configuration maps could therefore execute caller-controlled methods while
startup parsed optional production controls.

## Security

- `_optional_model_provider()`, `_optional_alert_webhook_url()`,
  `_optional_unpadded_control_free_str()`, `_optional_unpadded_control_free_setting()`,
  `_optional_admin_console_credential()`, and `_optional_openai_provider_value()` now route values
  through the shared exact-string runtime setting reader before optional blank handling.
- Values must be exact strings or `None`; string subclasses and non-string objects fail with
  `<SETTING> must be a string runtime setting`.
- The guard covers `JEDI_MODEL_PROVIDER`, `JEDI_ALERT_WEBHOOK_URL`, `JEDI_ADMIN_USERNAME`,
  `JEDI_ADMIN_PASSWORD`, `OPENAI_API_KEY`, `OPENAI_MODEL`, and shared optional unpadded runtime
  controls before `.strip()`, equality checks, URL validation, provider validation, admin credential
  byte-length checks, or runtime settings construction can run.
- Diagnostics name the setting and do not echo object type names, object string output, or
  credential-like fragments.

## Tests

- Added 1 failing-first optional model provider string-subclass assertion:
  `test_optional_model_provider_rejects_string_subclass_without_method_leak`.
- Added 1 failing-first optional alert webhook non-string assertion:
  `test_optional_alert_webhook_url_rejects_non_string_without_equality_leak`.
- Added 1 failing-first optional admin credential string-subclass assertion:
  `test_optional_admin_console_credential_rejects_string_subclass_without_method_leak`.
- Added 1 failing-first optional OpenAI setting string-subclass assertion:
  `test_optional_openai_provider_value_rejects_string_subclass_without_method_leak`.
- Added documentation coverage:
  `test_sprint_1026_documents_runtime_optional_setting_exact_string_guard`.

## Verification

- Focused tests failed before implementation because optional settings executed `.strip()` or
  equality hooks before rejecting malformed values.
- Focused runtime tests passed after implementation.
