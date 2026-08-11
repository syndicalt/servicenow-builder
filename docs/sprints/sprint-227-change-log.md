# Sprint 227 Change Log

Scope: Production hardening - bounded runtime request-id propagation.

## Changes

- Added regression coverage that runtime responses generate `X-JEDI-Request-ID` when no inbound request id exists.
- Added regression coverage that safe inbound `X-Request-ID` values are echoed as `X-JEDI-Request-ID`.
- Added regression coverage that overlong inbound request ids are not echoed and are replaced with generated UUID4 values.
- Added a centralized request-id response helper that accepts only printable ASCII request ids up to 128 characters.
- Documented that request ids are operator correlation metadata, not auth, idempotency, or lifecycle identity.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "request_id_header or inbound_request_id"` - 3 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 301 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1561 passed, 93.88% coverage.
