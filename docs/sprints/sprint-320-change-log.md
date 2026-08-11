# Sprint 320 Change Log - Provider Base URL Non-Public Host Guard

## Summary

- Shared model-provider `base_url` validation now rejects non-public host targets.
- OpenAI and Anthropic provider settings inherit the same local, private, link-local, reserved, multicast, unspecified, delegated `.localhost`, and legacy numeric local host guard.
- Provider endpoint diagnostics name `base_url` and do not echo the configured URL.
- Existing HTTPS, credential-free, query-free, fragment-free, length, and encoded-control validation remains intact.
- Documented the provider endpoint host boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_provider_settings_safety.py::test_validate_provider_base_url_rejects_non_public_hosts -q` - 9 tests failed before implementation because non-public provider hosts were accepted.
- `python3 -m pytest tests/test_provider_settings_safety.py tests/test_openai_provider.py::test_openai_provider_settings_reject_unsafe_base_url_shape tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_unsafe_base_url_shape -q` - 22 passed after implementation.
- `python3 -m ruff check src/jedi_devproject/provider_url_safety.py tests/test_provider_settings_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/provider_url_safety.py tests/test_provider_settings_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py` - no issues found in 4 source files.
- `python3 -m pytest tests/test_provider_settings_safety.py tests/test_openai_provider.py::test_openai_provider_settings_reject_unsafe_base_url_shape tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_unsafe_base_url_shape tests/test_project_docs.py::test_sprint_three_hundred_twenty_documents_provider_base_url_host_guard -q` - 23 passed.
- `python3 -m ruff check src/jedi_devproject/provider_url_safety.py tests/test_provider_settings_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/provider_url_safety.py tests/test_provider_settings_safety.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - no issues found in 5 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 394 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1923 passed, total coverage 93.87%.
