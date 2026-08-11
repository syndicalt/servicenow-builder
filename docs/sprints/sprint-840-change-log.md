# Sprint 840 Change Log - Admin rate limiter decision guard

## Intent

Harden admin runtime rate-limit enforcement so malformed limiter dependencies
fail closed with controlled diagnostics instead of surfacing raw runtime errors,
bypassing denial decisions, or producing invalid retry headers.

## Changes

- Added 1 failing-first malformed admin limiter decision assertion: `tests/test_runtime.py::test_admin_rate_limit_rejects_malformed_limiter_decisions`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_840_documents_admin_rate_limiter_decision_guard`.
- `_require_admin_rate_limit` now validates limiter decision objects and returns `admin rate limiter is invalid` before `Retry-After` header construction when the dependency returns malformed output.

## Verification

- `pytest tests/test_runtime.py::test_admin_rate_limit_rejects_malformed_limiter_decisions tests/test_project_docs.py::test_sprint_840_documents_admin_rate_limiter_decision_guard -q` - 7 passed.
- `pytest tests/test_runtime.py -q` - 411 passed.
- `pytest tests/test_project_docs.py -q` - 913 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3346 passed, 93.43% coverage.
