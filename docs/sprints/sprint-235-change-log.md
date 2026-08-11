# Sprint 235 Change Log

Scope: Production hardening - OpenAI model identifier character hygiene.

## Changes

- Added regression coverage that production validation rejects `OPENAI_MODEL` values containing control characters.
- Extended production runtime validation so OpenAI model identifiers must not contain whitespace or control characters when `JEDI_MODEL_PROVIDER=openai`.
- Documented that production model provider configuration must include both credential and model values free of whitespace/control characters.
- Preserved the existing fail-closed production requirement for explicit OpenAI provider configuration.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_openai_model_control_characters -q` - 1 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 309 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1578 passed, 93.90% coverage.
