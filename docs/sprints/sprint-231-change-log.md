# Sprint 231 Change Log

Scope: Production hardening - configured admin API token startup strength.

## Changes

- Added regression coverage that production validation rejects a configured `JEDI_ADMIN_API_TOKEN` shorter than 32 characters.
- Added `MIN_PRODUCTION_ADMIN_API_TOKEN_LENGTH = 32` in runtime configuration validation.
- Kept worker-only validation paths able to omit `JEDI_ADMIN_API_TOKEN`, while rejecting weak token values when the token is present.
- Documented the production admin API token strength rule in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_production_weak_admin_api_token -q` - 1 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 305 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1570 passed, 93.89% coverage.
