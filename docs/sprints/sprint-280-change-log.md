# Sprint 280 Change Log - Model Provider Encoded URL Control Guard

## Summary

- Provider `base_url` validation now rejects percent-encoded whitespace and control characters before URL parsing or outbound request construction.
- The shared model-provider base URL validator now reuses the existing encoded whitespace/control-character helper.
- OpenAI and Anthropic provider settings reject encoded newline and tab sequences in custom gateway endpoints.
- Existing provider empty-value, raw whitespace/control-character, HTTPS, hostname, credential, query, and fragment guards remain intact.
- Added failing regressions proving both adapters previously accepted encoded-control provider base URLs.
- Documented the provider encoded-control URL boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_reject_encoded_control_character_base_url tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_encoded_control_character_base_url -q` - 4 tests failed before implementation because both adapters accepted encoded-control provider base URLs.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` - 71 passed.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_eighty_documents_provider_encoded_url_control_guard -q` - 72 passed.
- `python3 -m ruff check src/jedi_devproject/provider_url_safety.py src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/provider_url_safety.py src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 6 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 176 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 354 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1715 passed; total coverage 93.98%.
