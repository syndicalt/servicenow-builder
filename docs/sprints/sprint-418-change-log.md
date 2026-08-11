# Sprint 418 Change Log

## Upper-bounded rate-limit windows

Added a hard upper bound for configured rate-limit windows. Prior hardening bounded request caps and bucket caps, but `window_seconds` still controlled how long request timestamp state could remain live in each bucket. An unsafe deployment override could set lifecycle or admin windows high enough to weaken stale-state pruning.

The shared `InMemoryRateLimiter` now rejects `window_seconds` values above `86400` seconds. Runtime validation applies the same ceiling to `JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS` and `JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS` before API construction. Validation diagnostics name the offending settings and approved ceiling without echoing the submitted excessive value.

This keeps rate-limit window tuning available while preserving a hard one-day retention ceiling for in-process limiter timestamp state.

## Verification

- Added 2 tests that failed before implementation because there was no window ceiling primitive or runtime validation for excessive windows.
- `python3 -m pytest tests/test_rate_limit.py tests/test_runtime.py -q -k "excessive"`: 8 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 191 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 492 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2245 total tests passed at 93.96% coverage.
