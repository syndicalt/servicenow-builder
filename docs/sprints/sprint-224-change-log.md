# Sprint 224 Change Log

Scope: Production hardening - failed admin authentication cache controls.

## Changes

- Added regression coverage that failed Bearer-token admin API authentication returns `Cache-Control: no-store`, `Pragma: no-cache`, `Expires: 0`, `Vary: Authorization`, and `X-Content-Type-Options: nosniff`.
- Added regression coverage that failed Basic-auth admin console authentication returns the same no-cache and credential-variation headers while preserving the `WWW-Authenticate` challenge.
- Added `Expires: 0` to the shared admin diagnostic response policy for legacy proxy and shared-workstation cache safety.
- Documented that admin diagnostic cache controls cover failed admin authentication responses as well as successful diagnostic views.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "auth_failure_is_not_cacheable"` - 2 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 298 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1550 passed, 93.90% coverage.
