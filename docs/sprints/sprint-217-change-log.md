# Sprint 217 Change Log

Scope: Production hardening - admin console rate-limit coverage.

## Changes

- Added regression coverage for repeated `/admin` HTML console requests.
- Added regression coverage for repeated `/admin/artifacts/{artifact_id}` Basic-auth artifact view requests.
- Wired the shared admin rate limiter into the HTML admin console route before Basic-auth credential checks.
- Wired the shared admin rate limiter into the Basic-auth admin artifact detail route before Basic-auth credential checks.
- Documented that JSON admin endpoints, artifact APIs, the HTML admin console, and Basic-auth artifact detail pages all share the same admin rate limiter.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_admin_console_rate_limits_repeated_requests tests/test_runtime.py::test_admin_console_artifact_view_rate_limits_repeated_requests tests/test_runtime.py::test_admin_jobs_rate_limits_repeated_requests tests/test_runtime.py::test_admin_jobs_uses_runtime_rate_limit_settings -q` - 4 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 291 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1524 passed, 93.99% coverage.
