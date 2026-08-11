# Sprint 321 Change Log - Provider Settings Validation Input Redaction

## Summary

- OpenAI provider settings now suppress rejected input values in Pydantic validation errors.
- Anthropic provider settings now suppress rejected input values in Pydantic validation errors.
- Malformed provider `base_url` diagnostics still name the field, but no longer echo metadata endpoint URLs, embedded credential userinfo, or raw configured URL fragments.
- Existing provider endpoint validation remains intact: unsafe shapes, non-public hosts, encoded controls, and oversized values still fail closed before any outbound request can be built.
- Documented the provider settings diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_validation_errors_do_not_echo_base_url tests/test_anthropic_provider.py::test_anthropic_provider_settings_validation_errors_do_not_echo_base_url -q` - 4 tests failed before implementation because provider settings validation errors included `input_value`.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_validation_errors_do_not_echo_base_url tests/test_anthropic_provider.py::test_anthropic_provider_settings_validation_errors_do_not_echo_base_url tests/test_openai_provider.py::test_openai_provider_settings_reject_unsafe_base_url_shape tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_unsafe_base_url_shape -q` - 14 passed after implementation.
- `python3 -m pytest tests/test_openai_provider.py::test_openai_provider_settings_validation_errors_do_not_echo_base_url tests/test_anthropic_provider.py::test_anthropic_provider_settings_validation_errors_do_not_echo_base_url tests/test_project_docs.py::test_sprint_three_hundred_twenty_one_documents_provider_settings_error_redaction -q` - 5 passed.
- `python3 -m ruff check src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/openai_provider.py src/jedi_devproject/anthropic_provider.py tests/test_openai_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - no issues found in 5 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 395 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1928 passed, total coverage 93.87%.
