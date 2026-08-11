# Sprint 1050 Change Log - Runtime handler model-routing direct settings boundary

## Summary

Sprint 1050 continued production hardening by tightening direct runtime fulfillment handler assembly. `process_one_runtime_fulfillment()` already validates `RuntimeSettings` before opening ServiceNow clients or the operational store, but embedded tests or future in-process callers can still assemble `_runtime_handler()` directly. That internal path read `RuntimeSettings.model_provider` and `RuntimeSettings.public_web_access` before applying exact-string guards, which allowed mutated settings objects to execute string-subclass hooks during `len()` or equality checks.

`_runtime_handler()` now normalizes model-provider, OpenAI provider, and public-web routing settings at the top of handler assembly. Malformed direct settings fail as `RuntimeConfigError` before provider construction, public documentation retriever construction, handler composition, or claim-handler execution.

## Changes

- `_runtime_handler()` now exact-string validates `RuntimeSettings.model_provider` before length, whitespace, and provider equality checks.
- `_runtime_handler()` now exact-string validates `RuntimeSettings.openai_api_key` and `RuntimeSettings.openai_model` before required-field checks and OpenAI provider settings construction.
- `_runtime_handler()` now exact-string validates `RuntimeSettings.public_web_access` before public documentation retriever equality checks.
- `_openai_provider_settings_from_runtime()` now reuses the direct exact-string boundary before creating `OpenAIProviderSettings`.
- Updated the operator guide to distinguish startup model-provider validation from internal runtime handler assembly validation.

## Tests

- Added 2 failing-first runtime handler boundary assertions:
  - `test_runtime_handler_rejects_model_provider_subclass_before_len`
  - `test_runtime_handler_rejects_public_web_access_subclass_before_eq`
- Initial focused run failed before implementation because `_runtime_handler()` executed string-subclass `__len__` and `__eq__` hooks.
- Focused regression after implementation:
  - `pytest tests/test_runtime.py -q -k "runtime_handler_rejects_model_provider_subclass or runtime_handler_rejects_public_web_access_subclass"` - 2 passed.
