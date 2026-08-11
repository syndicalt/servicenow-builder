# Sprint 279 Change Log - Model Provider Base URL Shape Guard

## Summary

- Added a shared model-provider base URL validator used by both OpenAI and Anthropic adapters.
- Provider `base_url` values must now be absolute HTTPS URLs with a hostname.
- Provider `base_url` values now reject embedded credentials, query parameters, and fragments before outbound request construction.
- Existing provider empty-value and whitespace/control-character guards remain intact.
- Added failing regressions proving both adapters previously accepted unsafe provider base URL shapes.
- Documented the provider base URL shape boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_reject_unsafe_base_url_shape tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_unsafe_base_url_shape -q` - 10 tests failed before implementation because both adapters accepted unsafe provider base URL shapes.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` - 67 passed.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_seventy_nine_documents_provider_base_url_shape_guard -q` - 68 passed.
- `python3 -m ruff check src/jedi_devproject/provider_url_safety.py src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/provider_url_safety.py src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 6 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 176 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 353 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1710 passed; total coverage 93.97%.
