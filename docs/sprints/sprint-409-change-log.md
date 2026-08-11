# Sprint 409 Change Log

## Configured lifecycle webhook secret validation

Hardened lifecycle webhook authentication so malformed configured webhook secrets are rejected at the API auth boundary before request authentication runs. Prior hardening validated inbound timestamp, signature, and shared-secret headers, but `_configured_webhook_secret()` only rejected missing values.

Configured lifecycle webhook secrets now reuse the same ASCII-only, no-padding, no-control-character, and 8 KiB byte-length boundary as inbound lifecycle credential material. Empty secrets continue to fail as unconfigured, while non-ASCII, padded, control-character-bearing, and oversized configured secrets fail closed as invalid runtime configuration with `503`.

## Tests

- Failing-first coverage: 4 tests failed before implementation, proving malformed configured webhook secrets were accepted.
- Focused verification: `python3 -m pytest tests/test_lifecycle_api.py -q -k "malformed_configured_secret"` passed with 4 tests.
- Broader lifecycle verification: `python3 -m pytest tests/test_lifecycle_api.py -q` passed with 40 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff format src/jedi_devproject/lifecycle_api.py tests/test_lifecycle_api.py tests/test_project_docs.py && python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 483 documentation tests passed, and 2207 total tests passed at 93.95% coverage.
