# Sprint 756 Change Log - Runtime OpenAI provider runtime cause boundary

## Scope

Hardened worker-side OpenAI provider construction so malformed direct `RuntimeSettings` values do not retain unsafe Pydantic validation exceptions as public `RuntimeConfigError` causes.

## Tests First

- Added 2 failing-first runtime OpenAI provider runtime cause assertions through the existing parametrized test:
  `tests/test_runtime.py::test_process_one_runtime_fulfillment_wraps_invalid_openai_provider_settings`
- Initial failures proved invalid `openai_api_key` and `openai_model` values raised `RuntimeConfigError` while retaining the original `OpenAIProviderSettings` validation error as `__cause__`.
- The malformed values included `openai-key` and model fallback fragments to prove cause retention could preserve configured provider values or validation metadata even though the public diagnostic named only the setting.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_756_documents_runtime_openai_provider_runtime_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original Pydantic validation causes in `_openai_provider_settings_from_runtime()`.
- Preserved existing fixed diagnostics:
  - `Invalid OpenAI provider runtime settings: OPENAI_API_KEY`
  - `Invalid OpenAI provider runtime settings: OPENAI_MODEL`
- Documented the runtime OpenAI provider runtime cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k process_one_runtime_fulfillment_wraps_invalid_openai_provider_settings` failed first, then passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_756` failed first, then passed.
- `ruff check src tests` passed.
- `mypy src tests` passed.
- `python3 -m pytest tests/test_runtime.py -q -k "process_one_runtime_fulfillment_wraps_invalid_openai_provider_settings or openai_runtime_error_fields"` passed: 3 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed: 3094 passed, 93.38% coverage.
