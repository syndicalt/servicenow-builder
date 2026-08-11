# Sprint 232 Change Log

Scope: Production hardening - admin API token character hygiene.

## Changes

- Added regression coverage that production validation rejects configured `JEDI_ADMIN_API_TOKEN` values containing control characters.
- Extended production runtime validation so configured admin API tokens must not contain whitespace or control characters.
- Documented that production admin API tokens must be both long enough and free of whitespace/control characters.
- Preserved worker-only validation paths that omit `JEDI_ADMIN_API_TOKEN` while rejecting malformed token values when present.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_admin_api_token_control_characters -q` - 1 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 306 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1572 passed, 93.89% coverage.
