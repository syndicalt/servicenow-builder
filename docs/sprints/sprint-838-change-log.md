# Sprint 838 Change Log - Rate limiter clock value guard

## Intent

Harden the shared in-memory rate limiter so injected clock callbacks cannot
return booleans, non-numeric values, non-finite values, or negative timestamps
that produce raw Python errors or unsafe bucket timestamps.

## Changes

- Added 1 failing-first rate limiter clock assertion: `tests/test_rate_limit.py::test_rate_limiter_rejects_invalid_clock_values_before_bucket_storage`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_838_documents_rate_limiter_clock_value_guard`.
- `InMemoryRateLimiter` now rejects invalid clock values with `rate limit clock must return a finite non-negative number` before bucket storage.
- Invalid booleans, non-numeric values, non-finite values, and negative timestamps fail before `_last_now` or bucket timestamp state is updated.

## Verification

- `pytest tests/test_rate_limit.py::test_rate_limiter_rejects_invalid_clock_values_before_bucket_storage tests/test_rate_limit.py::test_rate_limiter_clamps_backward_clock_before_storing_timestamps tests/test_project_docs.py::test_sprint_838_documents_rate_limiter_clock_value_guard -q` - 3 passed.
- `pytest tests/test_rate_limit.py -q` - 14 passed.
- `pytest tests/test_project_docs.py -q` - 911 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3337 passed, 93.42% coverage.
