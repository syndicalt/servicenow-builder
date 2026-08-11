# Sprint 419 Change Log

## Backward-clock-safe rate limiting

Hardened the shared `InMemoryRateLimiter` against backward process-clock movement. Prior behavior trusted each clock reading directly, so a backward clock step could inflate `Retry-After` calculations and append older timestamps into a limiter bucket.

The limiter now tracks the last observed time and clamps future reads so observed limiter time never moves backward within the process. If the underlying clock returns a lower value, rate-limit pruning, retry calculations, and stored timestamps use the last observed limiter time instead.

This keeps lifecycle webhook and admin diagnostic throttling deterministic across process clock adjustments while preserving existing behavior for forward-moving time.

## Verification

- Added 2 tests that failed before implementation because backward clock movement inflated `Retry-After` and stored older timestamps.
- `python3 -m pytest tests/test_rate_limit.py -q`: 10 tests passed.
- `python3 -m pytest tests/test_lifecycle_api.py tests/test_runtime.py -q -k "rate_limit or rate_limits"`: 19 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 191 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 493 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2248 total tests passed at 93.96% coverage.
