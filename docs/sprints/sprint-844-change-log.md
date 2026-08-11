# Sprint 844 Change Log - Provider base URL exact-string guard

## Intent

Harden model provider endpoint validation so direct callers cannot pass
non-string values or string subclasses into URL parsing and endpoint safety
helpers before provider request construction.

## Changes

- Added 1 failing-first provider base URL exact-string assertion: `tests/test_provider_settings_safety.py::test_validate_provider_base_url_rejects_non_exact_strings`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_844_documents_provider_base_url_exact_string_guard`.
- `validate_provider_base_url()` now rejects non-exact strings with `base_url must be an exact string` before URL parsing or endpoint safety checks.

## Verification

- `pytest tests/test_provider_settings_safety.py::test_validate_provider_base_url_rejects_non_exact_strings tests/test_project_docs.py::test_sprint_844_documents_provider_base_url_exact_string_guard -q` - 5 passed.
- `pytest tests/test_provider_settings_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py -q` - 167 passed.
- `pytest tests/test_project_docs.py -q` - 917 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3363 passed, 93.44% coverage.
