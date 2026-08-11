# Sprint 413 Change Log

## Bounded rate-limit bucket keys

Hardened the shared `InMemoryRateLimiter` so caller-provided bucket keys are bounded and sanitized before storage. Prior limiter state used the raw key string as the dictionary key, which meant a malformed lifecycle client host/path value or future caller-provided identifier could persist oversized strings, control characters, non-ASCII data, or secret-bearing fragments in process memory.

Safe printable ASCII keys up to 256 bytes are preserved. Oversized, whitespace-bearing, control-character-bearing, or non-ASCII keys are replaced with deterministic `sha256:<digest>` bucket identifiers before lookup or insertion. The original malformed key still maps consistently within the limiter window, but the limiter does not retain the raw value.

This hardens both lifecycle webhook rate limiting and admin diagnostic rate limiting because both use the shared limiter primitive.

## Verification

- Added 3 tests that failed before implementation because the shared limiter had no explicit bucket-key boundary and stored raw caller-provided keys.
- `python3 -m pytest tests/test_rate_limit.py -q`: 3 tests passed.
- `python3 -m pytest tests/test_lifecycle_api.py tests/test_runtime.py -q -k "rate_limit or rate_limits"`: 11 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 190 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 487 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2227 total tests passed at 93.95% coverage.
