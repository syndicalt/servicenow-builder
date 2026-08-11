# Sprint 841 Change Log - Lifecycle rate limiter decision guard

## Intent

Harden lifecycle webhook rate-limit enforcement so malformed limiter
dependencies fail closed before request handling can crash, bypass throttling,
record webhook events behind a broken limiter, or emit invalid retry metadata.

## Changes

- Added 1 failing-first malformed lifecycle limiter decision assertion: `tests/test_lifecycle_api.py::test_lifecycle_rate_limit_rejects_malformed_limiter_decisions`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_841_documents_lifecycle_rate_limiter_decision_guard`.
- `_require_rate_limit` now validates lifecycle limiter decision objects and returns `lifecycle rate limiter is invalid` before lifecycle `Retry-After` header construction when the dependency returns malformed output.
- Shared limiter decision shape validation now lives in `rate_limit.py` so admin and lifecycle adapters use the same production boundary check while keeping domain-specific diagnostics.

## Verification

- `pytest tests/test_lifecycle_api.py::test_lifecycle_rate_limit_rejects_malformed_limiter_decisions tests/test_project_docs.py::test_sprint_841_documents_lifecycle_rate_limiter_decision_guard -q` - 7 passed.
- `pytest tests/test_lifecycle_api.py::test_lifecycle_rate_limit_rejects_malformed_limiter_decisions tests/test_runtime.py::test_admin_rate_limit_rejects_malformed_limiter_decisions tests/test_project_docs.py::test_sprint_841_documents_lifecycle_rate_limiter_decision_guard tests/test_project_docs.py::test_sprint_840_documents_admin_rate_limiter_decision_guard -q` - 14 passed.
- `pytest tests/test_rate_limit.py -q` - 15 passed.
- `pytest tests/test_runtime.py -q` - 411 passed.
- `pytest tests/test_lifecycle_api.py -q` - 56 passed.
- `pytest tests/test_project_docs.py -q` - 914 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3353 passed, 93.43% coverage.
