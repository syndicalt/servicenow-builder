# Sprint 277 Change Log - Model Provider Empty Credential Guard

## Summary

- OpenAI provider settings now reject empty `api_key` and `model` values before outbound request construction.
- Anthropic provider settings now reject empty `api_key` and `model` values before outbound request construction.
- Existing provider whitespace and control-character guards remain intact.
- Added failing regressions proving both adapters previously accepted empty provider credentials and model identifiers.
- Documented the provider empty-value boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_reject_empty_api_key tests/test_openai_provider.py::test_openai_provider_settings_reject_empty_model tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_empty_api_key tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_empty_model -q` - 4 tests failed before implementation because both adapters accepted empty provider credentials and model identifiers.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` - 55 passed.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_seventy_seven_documents_provider_empty_value_guard -q` - 56 passed.
- `python3 -m ruff check src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 5 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 351 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1696 passed; total coverage 93.96%.
