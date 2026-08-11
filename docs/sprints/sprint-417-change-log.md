# Sprint 417 Change Log

## Upper-bounded rate-limit request caps

Added a hard upper bound for configured rate-limit request caps. Prior hardening bounded bucket key material and bucket cardinality, but `max_requests` still controlled the maximum timestamp deque length for each bucket. An unsafe deployment override could set lifecycle or admin request caps high enough to weaken the per-bucket memory boundary.

The shared `InMemoryRateLimiter` now rejects `max_requests` values above `10000`. Runtime validation applies the same ceiling to `JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS` and `JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS` before API construction. Validation diagnostics name the offending settings and approved ceiling without echoing the submitted excessive value.

This keeps request-rate tuning available while preserving a hard per-bucket memory ceiling for lifecycle webhook and admin diagnostic ingress.

## Verification

- Added 2 tests that failed before implementation because there was no max-request ceiling primitive or runtime validation for excessive request caps.
- `python3 -m pytest tests/test_rate_limit.py tests/test_runtime.py -q -k "excessive"`: 6 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 191 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 491 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2242 total tests passed at 93.96% coverage.
