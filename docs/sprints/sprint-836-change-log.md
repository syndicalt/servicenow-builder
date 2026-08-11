# Sprint 836 Change Log - Rate limiter direct numeric guard

## Intent

Harden the shared in-memory rate limiter so direct construction cannot accept
boolean numeric controls or fail with raw Python type errors for non-integer
controls. Runtime settings already parse environment values, but the limiter is
a shared abuse-control primitive and must protect its own boundary.

## Changes

- Added 1 failing-first rate limiter numeric assertion: `tests/test_rate_limit.py::test_rate_limiter_rejects_invalid_direct_numeric_controls`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_836_documents_rate_limiter_direct_numeric_guard`.
- `InMemoryRateLimiter` now rejects boolean and non-integer `max_requests`, `window_seconds`, and `max_buckets` values before range checks or bucket state initialization.
- Invalid direct controls fail with stable diagnostics: `max_requests must be an integer`, `window_seconds must be an integer`, or `max_buckets must be an integer`.

## Verification

- `pytest tests/test_rate_limit.py::test_rate_limiter_rejects_invalid_direct_numeric_controls tests/test_rate_limit.py::test_rate_limiter_preserves_safe_bucket_keys tests/test_project_docs.py::test_sprint_836_documents_rate_limiter_direct_numeric_guard -q` - 3 passed.
- `pytest tests/test_rate_limit.py -q` - 12 passed.
- `pytest tests/test_project_docs.py -q` - 909 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3333 passed, 93.42% coverage.
