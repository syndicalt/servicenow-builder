# Sprint 233 Change Log

Scope: Production hardening - HMAC lifecycle webhook secret character hygiene.

## Changes

- Added regression coverage that production validation rejects `JEDI_LIFECYCLE_WEBHOOK_SECRET` values containing control characters.
- Extended production runtime validation so HMAC webhook secrets must not contain whitespace or control characters.
- Documented that production webhook secrets must be both long enough and free of whitespace/control characters.
- Preserved the existing fail-closed production requirement for `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256`.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_webhook_secret_control_characters -q` - 1 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 307 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1574 passed, 93.89% coverage.
