# Sprint 282 Change Log - Model Provider Base URL Length Bound

## Summary

- Added a shared `MAX_PROVIDER_BASE_URL_CHARS` bound of 2048 characters for model-provider endpoint configuration.
- OpenAI and Anthropic provider `base_url` settings now reject oversized endpoint values before decode, URL parsing, or outbound request construction.
- Existing provider empty-value, raw whitespace/control-character, encoded-control, HTTPS, hostname, credential, query, and fragment guards remain intact.
- Custom provider gateways remain supported when their base endpoint fits the documented bound.
- Added failing regressions proving both adapters previously accepted oversized provider base URLs.
- Documented the provider base URL length boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_reject_oversized_base_url tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_oversized_base_url -q` - 2 tests failed before implementation because both adapters accepted oversized provider base URLs.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` - 77 passed.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_eighty_two_documents_provider_base_url_length_bound -q` - 78 passed.
- `python3 -m ruff check src/jedi_devproject/provider_url_safety.py src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/provider_url_safety.py src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 6 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 177 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 356 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1726 passed; total coverage 93.97%.
