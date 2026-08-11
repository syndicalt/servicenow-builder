# Sprint 416 Change Log

## Upper-bounded rate-limit bucket caps

Added a hard upper bound for configured rate-limit bucket cardinality. Sprint 415 made lifecycle and admin bucket caps configurable, but without an upper ceiling an operator typo or unsafe deployment override could still weaken the memory boundary by setting a very large bucket cap.

The shared `InMemoryRateLimiter` now rejects `max_buckets` values above `100000`. Runtime validation applies the same ceiling to `JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS` and `JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS` before API construction. Validation diagnostics name the offending settings and the approved ceiling without echoing the submitted oversized value.

This keeps bucket cardinality tunable while preserving a production memory hardening limit that cannot be bypassed through configuration alone.

## Verification

- Added 2 tests that failed before implementation because there was no max-bucket ceiling primitive or runtime validation for excessive bucket caps.
- `python3 -m pytest tests/test_rate_limit.py tests/test_runtime.py -q -k "excessive"`: 4 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 191 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 490 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2239 total tests passed at 93.95% coverage.
