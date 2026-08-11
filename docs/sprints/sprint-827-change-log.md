# Sprint 827 Change Log - Runtime rate-limiter fail-closed construction

## Scope

Hardened runtime API construction so invalid lifecycle or admin rate-limit settings cannot silently disable request limiting in direct `RuntimeSettings` paths.

## Tests First

- Added 1 failing-first runtime API rate-limit construction assertion: `tests/test_runtime.py::test_runtime_api_rejects_non_positive_rate_limit_settings_before_serving`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_827_documents_runtime_rate_limiter_fail_closed_construction`.
- Initial failure proved zero request/window settings disabled the runtime limiter, and zero bucket settings escaped as raw `ValueError` instead of stable runtime configuration diagnostics.

## Changes

- Runtime lifecycle and admin limiter construction now rejects non-positive request, window, and bucket settings with `RuntimeConfigError` before route serving.
- The fail-closed construction covers `JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS`, `JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS`, `JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS`, `JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS`, `JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS`, and `JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS`.
- Runtime limiter construction wraps `InMemoryRateLimiter` ceiling errors with the relevant environment setting name.
- Updated the operator guide to document that runtime API construction rejects non-positive rate-limit settings instead of silently disabling limiters.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "runtime_api_rejects_non_positive_rate_limit_settings_before_serving or admin_jobs_uses_runtime_rate_limit_settings or admin_rate_limiter_uses_runtime_bucket_cap"` - 8 passed, 379 deselected.
- `python3 -m pytest tests/test_rate_limit.py -q` - 11 passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_827` - 1 passed, 899 deselected.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 202 source files.
- `python3 -m pytest tests/test_runtime.py -q` - 387 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3266 passed, 93.36% coverage.
