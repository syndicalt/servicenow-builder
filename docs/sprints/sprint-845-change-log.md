# Sprint 845 Change Log - Provider token exact-string guard

## Intent

Harden model provider credential and model validation so direct callers cannot
pass non-string values or string subclasses into provider token length,
whitespace, or control-character checks before adapter construction.

## Changes

- Added 1 failing-first provider token exact-string assertion: `tests/test_provider_settings_safety.py::test_validate_provider_tokens_reject_non_exact_strings`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_845_documents_provider_token_exact_string_guard`.
- `validate_provider_api_key()` now rejects non-exact strings with `api_key must be an exact string`.
- `validate_provider_model()` now rejects non-exact strings with `model must be an exact string`.

## Verification

- `pytest tests/test_provider_settings_safety.py::test_validate_provider_tokens_reject_non_exact_strings tests/test_project_docs.py::test_sprint_845_documents_provider_token_exact_string_guard -q` - 9 passed.
- `pytest tests/test_provider_settings_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py -q` - 175 passed.
- `pytest tests/test_project_docs.py -q` - 918 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3372 passed, 93.44% coverage.
