# Sprint 837 Change Log - Rate limiter direct key guard

## Intent

Harden the shared in-memory rate limiter so direct callers cannot pass
non-string, string-subclass, or object-backed bucket keys that fail with raw
attribute errors or invoke caller-controlled string methods before the limiter
touches process state.

## Changes

- Added 1 failing-first rate limiter key assertion: `tests/test_rate_limit.py::test_rate_limiter_rejects_non_exact_string_keys_before_state_access`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_837_documents_rate_limiter_direct_key_guard`.
- `InMemoryRateLimiter.check()` now rejects non-exact-string keys with `rate limit key must be an exact string` before clock reads or bucket state access.
- The guard prevents bytes, nulls, numeric values, string subclasses, or objects with caller-controlled string methods from reaching key hashing or bucket storage.

## Verification

- `pytest tests/test_rate_limit.py::test_rate_limiter_rejects_non_exact_string_keys_before_state_access tests/test_rate_limit.py::test_rate_limiter_preserves_safe_bucket_keys tests/test_project_docs.py::test_sprint_837_documents_rate_limiter_direct_key_guard -q` - 3 passed.
- `pytest tests/test_rate_limit.py -q` - 13 passed.
- `pytest tests/test_project_docs.py -q` - 910 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3335 passed, 93.42% coverage.
