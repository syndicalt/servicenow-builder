# Sprint 411 Change Log

## Configured admin console credential validation

Hardened development Basic-auth console authentication so malformed configured console credentials are rejected before inbound Basic-auth payloads are decoded or compared. Prior runtime settings loading rejected malformed `JEDI_ADMIN_CONSOLE_USERNAME` and `JEDI_ADMIN_CONSOLE_PASSWORD` values, but `_require_admin_console_credentials()` trusted the `RuntimeSettings` object and only validated decoded inbound Basic-auth credential parts.

Configured console username and password values now fail closed at the auth boundary when they are non-ASCII, padded, control-character-bearing, or larger than the 8 KiB Basic-auth credential boundary. Blank or absent configured values still fail as unconfigured. Malformed configured values return `503 admin console credentials are invalid` before Basic-auth decoding and before any constant-time credential comparison runs.

This keeps direct `RuntimeSettings` construction, tests, and future alternate configuration loaders aligned with the production hardening posture for admin diagnostic ingress.

## Verification

- Added 8 tests that failed before implementation because malformed configured console credentials allowed inbound Basic-auth decoding to run.
- `python3 -m pytest tests/test_runtime.py -q -k "admin_console_rejects_malformed_configured_credentials_before_decode or admin_basic_auth or basic_auth_decoder or admin_bearer_token"`: 24 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 190 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 485 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2221 total tests passed at 93.95% coverage.
