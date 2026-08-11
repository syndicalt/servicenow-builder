# Sprint 420 Change Log

## Concurrent-safe rate limiting

Hardened the shared `InMemoryRateLimiter` against concurrent request races. Prior behavior mutated bucket state without a critical section, so two runtime request threads could both observe the same pre-admission bucket length and both append timestamps even when `max_requests=1`.

The limiter now serializes bucket lookup, expired-bucket pruning, overflow routing, retry calculation, and timestamp append with a process-local lock. This keeps lifecycle webhook throttling and admin diagnostic throttling deterministic under concurrent request bursts.

This remains a per-process limiter. Federal production deployments should still enforce distributed rate controls at the approved edge, WAF, ingress, or API gateway boundary.

## Verification

- Added 1 concurrency test that failed before implementation because two concurrent checks were both admitted with `max_requests=1`.
- `python3 -m pytest tests/test_rate_limit.py -q -k "serializes_concurrent"`: failed before implementation with 2 allowed decisions.
- `python3 -m pytest tests/test_rate_limit.py -q`: 11 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 191 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 494 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2250 total tests passed at 93.96% coverage.
