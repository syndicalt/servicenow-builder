# Sprint 839 Change Log - Rate limiter clock callable guard

## Intent

Harden the shared in-memory rate limiter so malformed injected clock
dependencies fail at construction instead of producing raw runtime errors when
the limiter is first checked.

## Changes

- Added 1 failing-first rate limiter clock callable assertion: `tests/test_rate_limit.py::test_rate_limiter_rejects_non_callable_clock_at_construction`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_839_documents_rate_limiter_clock_callable_guard`.
- `InMemoryRateLimiter` now rejects non-callable `clock` dependencies with `rate limit clock must be callable` before limiter state initialization.

## Verification

- `pytest tests/test_rate_limit.py::test_rate_limiter_rejects_non_callable_clock_at_construction tests/test_rate_limit.py::test_rate_limiter_preserves_safe_bucket_keys tests/test_project_docs.py::test_sprint_839_documents_rate_limiter_clock_callable_guard -q` - 3 passed.
- `pytest tests/test_rate_limit.py -q` - 15 passed.
- `pytest tests/test_project_docs.py -q` - 912 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3339 passed, 93.43% coverage.
