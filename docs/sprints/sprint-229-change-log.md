# Sprint 229 Change Log

Scope: Production hardening - bounded Bearer admin token comparison.

## Changes

- Added regression coverage that oversized Bearer admin tokens are rejected before `secrets.compare_digest()` is called.
- Added an explicit 8192-byte token-value limit for admin Bearer token checks.
- Preserved fail-closed rejected-token behavior for oversized Bearer tokens.
- Documented that oversized token probes cannot create an unbounded comparison path.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_admin_bearer_token_rejects_oversized_token_before_compare -q` - 1 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 303 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1565 passed, 93.88% coverage.
