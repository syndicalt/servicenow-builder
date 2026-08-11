# Sprint 760 Change Log - Anthropic max-tokens cause boundary

## Scope

Hardened Anthropic provider environment parsing so malformed `ANTHROPIC_MAX_TOKENS` values do not retain unsafe strict numeric parser exceptions as public provider configuration causes.

## Tests First

- Added 1 failing-first Anthropic provider config cause assertion:
  - `tests/test_anthropic_provider.py::test_settings_from_env_rejects_non_numeric_max_tokens`
- Initial failure proved malformed `ANTHROPIC_MAX_TOKENS` retained the strict parser `ValueError` on `AnthropicProviderConfigError.__cause__`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_760_documents_anthropic_max_tokens_cause_boundary`
- The documentation assertion was added before the sprint log and operator guide update, so the docs gate covers the new operator-facing contract.

## Changes

- Suppressed original strict numeric parser causes when `ANTHROPIC_MAX_TOKENS` is malformed.
- Preserved the fixed diagnostic naming `ANTHROPIC_MAX_TOKENS` and the ASCII base-10 digits requirement.
- Documented the Anthropic max-token cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_anthropic_provider.py -q -k non_numeric_max_tokens` - 1 passed, 98 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_760` - 1 passed, 833 deselected.
- `python3 -m pytest tests/test_anthropic_provider.py -q` - 99 passed.
- `ruff check src tests` - passed.
- `mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3103 passed, 93.39% coverage.
