# Sprint 284 Change Log - Anthropic Max Tokens Bound

## Summary

- Added a named `MAX_ANTHROPIC_MAX_TOKENS` ceiling of 128000 tokens for Anthropic provider settings.
- Direct `AnthropicProviderSettings` construction now rejects oversized `max_tokens` values before request construction.
- `ANTHROPIC_MAX_TOKENS` env parsing now rejects oversized values before returning provider settings.
- Existing positive, non-numeric, and non-positive max-token validation remains intact.
- Added failing regressions proving direct and env-derived Anthropic settings previously accepted oversized token budgets.
- Documented the Anthropic max-token boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_settings_reject_oversized_max_tokens tests/test_anthropic_provider.py::test_settings_from_env_rejects_oversized_max_tokens -q` - 2 tests failed before implementation because direct and env-derived Anthropic settings accepted oversized token budgets.
- `python3 -m pytest tests/test_anthropic_provider.py -q` - 58 passed.
- `python3 -m pytest tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_eighty_four_documents_anthropic_max_tokens_bound -q` - 59 passed.
- `python3 -m ruff check src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 358 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1737 passed; total coverage 93.98%.
