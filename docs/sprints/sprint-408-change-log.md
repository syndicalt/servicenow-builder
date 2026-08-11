# Sprint 408 Change Log

## Shaped lifecycle HMAC signatures

Hardened lifecycle webhook HMAC authentication so malformed signature headers are rejected before constant-time comparison. Earlier hardening rejected missing, padded, control-character-bearing, oversized, and non-ASCII signatures, but unsupported signature schemes and malformed digest bodies could still reach `hmac.compare_digest()`.

Lifecycle HMAC signatures now must match one of two supported shapes before comparison: `sha256=` followed by exactly 64 hexadecimal characters, or `sha256-base64=` followed by Base64 that decodes to a 32-byte SHA-256 MAC. Unsupported prefixes, malformed hex, and invalid Base64 are rejected with the existing `lifecycle webhook signature rejected` diagnostic.

## Tests

- Failing-first coverage: 3 tests failed before implementation, proving unsupported signature prefixes, malformed hex signatures, and malformed Base64 signatures reached constant-time comparison.
- Focused verification: `python3 -m pytest tests/test_lifecycle_api.py -q -k "malformed_signature_shape_before_compare"` passed with 3 tests.
- Broader lifecycle verification: `python3 -m pytest tests/test_lifecycle_api.py -q` passed with 36 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff format src/jedi_devproject/lifecycle_api.py tests/test_lifecycle_api.py tests/test_project_docs.py && python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 482 documentation tests passed, and 2202 total tests passed at 93.94% coverage.
