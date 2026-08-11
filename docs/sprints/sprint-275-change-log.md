# Sprint 275 Change Log - Model Provider Base URL Control Character Guard

## Summary

- OpenAI provider settings now reject `base_url` values containing whitespace or control characters before outbound request construction.
- Anthropic provider settings now reject `base_url` values containing whitespace or control characters before outbound request construction.
- Custom model gateway endpoints remain supported when they are single-token URLs suitable for transport construction.
- Added failing regressions proving both adapters previously accepted newline-bearing provider base URLs.
- Documented the model provider base URL boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_reject_control_character_base_url tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_control_character_base_url -q` - 2 tests failed before implementation because both adapters accepted newline-bearing provider base URLs.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` - 47 passed.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_seventy_five_documents_provider_base_url_guard -q` - 48 passed.
- `python3 -m ruff check src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 5 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 349 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1686 passed; total coverage 93.95%.
