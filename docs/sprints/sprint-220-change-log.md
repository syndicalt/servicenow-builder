# Sprint 220 Change Log

Scope: Production hardening - admin diagnostic response headers.

## Changes

- Added regression coverage for admin JSON diagnostics returning `Cache-Control: no-store`, `Pragma: no-cache`, and `X-Content-Type-Options: nosniff`.
- Added regression coverage for the HTML admin console and Basic-auth artifact detail pages returning the same non-cacheable diagnostic response headers.
- Added runtime middleware that applies `X-Content-Type-Options: nosniff` to all runtime responses.
- Kept cache prevention scoped to admin diagnostic paths so `/health` receives `nosniff` without forced `no-store` probe semantics.
- Documented that admin diagnostic responses are non-cacheable and that liveness/readiness probes keep narrow browser hardening.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "diagnostics_are_not_cacheable or liveness_disables_sniffing"` - 4 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 294 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1534 passed, 93.96% coverage.
