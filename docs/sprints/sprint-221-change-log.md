# Sprint 221 Change Log

Scope: Production hardening - HTML admin console browser isolation headers.

## Changes

- Added regression coverage for `/admin` returning a restrictive `Content-Security-Policy`, `X-Frame-Options: DENY`, and `Referrer-Policy: no-referrer`.
- Added regression coverage for `/admin/artifacts/{artifact_id}` returning the same HTML browser isolation headers.
- Added regression coverage that JSON admin diagnostics such as `/admin/jobs` do not receive the HTML CSP.
- Added a path-scoped HTML response policy for the admin console and Basic-auth artifact pages.
- Documented the CSP resource model, framing denial, referrer suppression, and JSON/HTML boundary.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "browser_security_headers or html_csp"` - 3 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 295 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1538 passed, 93.94% coverage.
