# Sprint 278 Change Log - Model Provider Empty Base URL Guard

## Summary

- OpenAI provider settings now reject empty `base_url` values before outbound request construction.
- Anthropic provider settings now reject empty `base_url` values before outbound request construction.
- Existing provider empty credential/model and whitespace/control-character guards remain intact.
- Added failing regressions proving both adapters previously accepted empty provider base URLs.
- Documented the provider empty base URL boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_reject_empty_base_url tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_empty_base_url -q` - 2 tests failed before implementation because both adapters accepted empty provider base URLs.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` - 57 passed.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_seventy_eight_documents_provider_empty_base_url_guard -q` - 58 passed.
- `python3 -m ruff check src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 5 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 352 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1699 passed; total coverage 93.97%.
