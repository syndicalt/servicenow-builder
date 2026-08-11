# Sprint 414 Change Log

## Capped rate-limit bucket cardinality

Hardened the shared `InMemoryRateLimiter` so live bucket count is bounded in addition to bucket key content. Prior hardening sanitized raw key material, but high-cardinality caller identity values could still create unbounded per-process limiter buckets until process restart or external traffic controls intervened.

The limiter now prunes expired buckets on every check and defaults to at most 10000 live buckets. If a new bucket arrives while the limiter remains at capacity after pruning, that request is assigned to a shared `rate-limit-overflow` bucket instead of creating another per-client bucket. The overflow bucket is deterministic and participates in the same request/window decision logic as normal buckets.

This keeps lifecycle webhook and admin diagnostic rate limiting bounded under high-cardinality source patterns while preserving existing route-level throttling behavior.

## Verification

- Added 2 tests that failed before implementation because the limiter had no max-bucket or overflow-bucket primitive.
- `python3 -m pytest tests/test_rate_limit.py -q`: 5 tests passed.
- `python3 -m pytest tests/test_lifecycle_api.py tests/test_runtime.py -q -k "rate_limit or rate_limits"`: 11 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 191 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 488 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2230 total tests passed at 93.95% coverage.
