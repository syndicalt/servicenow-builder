# Sprint 276 Change Log - Model Provider Credential Control Character Guard

## Summary

- OpenAI provider settings now reject `api_key` and `model` values containing whitespace or control characters before outbound request construction.
- Anthropic provider settings now reject `api_key` and `model` values containing whitespace or control characters before outbound request construction.
- Existing provider `base_url` control-character guards remain intact.
- Added failing regressions proving both adapters previously accepted newline-bearing provider credentials and model identifiers.
- Documented the provider credential and model identifier boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_reject_control_character_api_key tests/test_openai_provider.py::test_openai_provider_settings_reject_control_character_model tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_control_character_api_key tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_control_character_model -q` - 4 tests failed before implementation because both adapters accepted newline-bearing provider credentials and model identifiers.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` - 51 passed.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_seventy_six_documents_provider_credential_guard -q` - 52 passed.
- `python3 -m ruff check src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 5 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 350 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1691 passed; total coverage 93.96%.
