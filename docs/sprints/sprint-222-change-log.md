# Sprint 222 Change Log

Scope: Production hardening - explicit Strict Transport Security response policy.

## Changes

- Added runtime settings for `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED` and `JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS`.
- Added regression coverage that the runtime does not emit `Strict-Transport-Security` by default.
- Added regression coverage that enabling HSTS emits `Strict-Transport-Security: max-age=31536000; includeSubDomains`.
- Added regression coverage that a configured max-age such as `63072000` is used in the emitted header.
- Added production startup validation for non-positive `JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS`.
- Documented that HSTS is deployment-controlled and should be enabled only after the public edge is permanently HTTPS.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "strict_transport_security or hsts or non_positive_runtime_limits"` - 5 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 296 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1543 passed, 93.95% coverage.
