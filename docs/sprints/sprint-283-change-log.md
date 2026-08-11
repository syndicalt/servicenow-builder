# Sprint 283 Change Log - Model Provider Credential and Model Length Bounds

## Summary

- Added shared provider setting validators for model-provider API keys and model identifiers.
- Provider `api_key` values now reject values longer than 4096 characters before transport construction.
- Provider `model` values now reject values longer than 256 characters before request construction.
- OpenAI and Anthropic provider settings now use the shared validators for non-empty, single-token, and bounded credential/model validation.
- Existing provider base URL length, URL shape, encoded-control, and raw control-character guards remain intact.
- Added failing regressions proving both adapters previously accepted oversized provider API keys and model identifiers.
- Documented the provider credential and model length boundaries in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_reject_oversized_api_key tests/test_openai_provider.py::test_openai_provider_settings_reject_oversized_model tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_oversized_api_key tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_oversized_model -q` - 4 tests failed before implementation because both adapters accepted oversized provider API keys and model identifiers.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` - 81 passed.
- `python3 -m pytest tests/test_provider_settings_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_eighty_three_documents_provider_setting_length_bounds -q` - 85 passed.
- `python3 -m ruff check src/jedi_devproject/provider_settings_safety.py src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_provider_settings_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/provider_settings_safety.py src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_provider_settings_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 7 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 357 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1734 passed; total coverage 93.98%.
