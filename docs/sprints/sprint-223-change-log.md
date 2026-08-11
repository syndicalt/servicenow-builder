# Sprint 223 Change Log

Scope: Production hardening - authenticated admin diagnostic cache variation.

## Changes

- Added regression coverage that JSON admin diagnostics such as `/admin/jobs` return `Vary: Authorization`.
- Added regression coverage that the HTML admin console returns `Vary: Authorization`.
- Added regression coverage that public probes such as `/health` do not emit `Vary: Authorization`.
- Added a shared helper that appends `Authorization` to an existing `Vary` response header without clobbering future route-specific values.
- Documented that authenticated admin diagnostic responses vary by credential context for shared proxy and cache safety.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "vary_by_authorization or liveness_does_not_vary"` - 3 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 297 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1547 passed, 93.91% coverage.
