# Sprint 410 Change Log

## Configured admin bearer token validation

Hardened admin API bearer authentication so malformed configured admin API tokens are rejected before inbound bearer credentials are compared. Prior runtime settings loading rejected malformed `JEDI_ADMIN_API_TOKEN` values, but `_require_admin_token()` trusted the `RuntimeSettings` object and only validated the inbound Bearer value.

Configured admin API tokens now reuse the same ASCII-only, no-padding, no-control-character, and 8 KiB byte-length boundary as inbound Bearer token material at the auth boundary. Blank or absent configured tokens still fail as unconfigured, while non-ASCII, padded, control-character-bearing, and oversized configured tokens fail closed as invalid runtime configuration with `503 admin artifact API token is invalid`.

This keeps direct `RuntimeSettings` construction, tests, and future alternate configuration loaders aligned with the production startup boundary before any constant-time credential comparison runs.

## Verification

- Added 4 tests that failed before implementation because malformed configured admin tokens reached `secrets.compare_digest()`.
- `python3 -m pytest tests/test_runtime.py -q -k "admin_bearer_token"`: 9 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 190 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 484 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2212 total tests passed at 93.95% coverage.
