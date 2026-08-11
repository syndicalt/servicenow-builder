# Sprint 228 Change Log

Scope: Production hardening - bounded Basic auth credential decoding.

## Changes

- Added regression coverage that oversized Basic auth credential payloads are rejected before base64 decoding.
- Added an explicit 8192-byte encoded credential limit for development Basic auth parsing.
- Preserved fail-closed behavior for malformed or oversized Basic auth values.
- Documented that the Basic auth bound is separate from admin request body-size limits and rate limiting.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_basic_auth_decoder_rejects_oversized_payload_before_decode -q` - 1 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 302 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1563 passed, 93.88% coverage.
