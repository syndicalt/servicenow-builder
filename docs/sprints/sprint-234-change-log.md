# Sprint 234 Change Log

Scope: Production hardening - OpenAI provider credential character hygiene.

## Changes

- Added regression coverage that production validation rejects `OPENAI_API_KEY` values containing control characters.
- Extended production runtime validation so OpenAI API keys must not contain whitespace or control characters when `JEDI_MODEL_PROVIDER=openai`.
- Documented that production model provider credentials must be present and free of whitespace/control characters.
- Preserved the existing fail-closed production requirement for explicit OpenAI provider configuration.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_openai_api_key_control_characters -q` - 1 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 308 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1576 passed, 93.90% coverage.
