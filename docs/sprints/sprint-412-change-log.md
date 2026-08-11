# Sprint 412 Change Log

## ASCII-only Basic-auth encoded payloads

Hardened development Basic-auth console parsing so non-ASCII encoded credential sections are rejected before Base64 decoding. Prior bounds rejected padded, whitespace-bearing, control-character-bearing, and oversized encoded sections, but a non-ASCII Basic-auth payload could still reach `base64.b64decode()`.

The encoded credential section now must encode as ASCII before decoding, and the 8 KiB limit is measured on encoded ASCII bytes. Non-ASCII encoded payloads return the normal unauthenticated Basic-auth response path before Base64 decoding and before any constant-time credential comparison runs.

This keeps malformed admin console ingress inside the same deterministic rejection path as other invalid Basic-auth payload shapes.

## Verification

- Added 1 test that failed before implementation because a non-ASCII encoded Basic-auth payload reached `base64.b64decode()`.
- `python3 -m pytest tests/test_runtime.py -q -k "basic_auth_decoder or admin_basic_auth or admin_console_rejects_malformed_configured_credentials_before_decode or admin_bearer_token"`: 25 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 190 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 486 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2223 total tests passed at 93.95% coverage.
