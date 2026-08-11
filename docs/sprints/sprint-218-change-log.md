# Sprint 218 Change Log

Scope: Production hardening - admin artifact payload redaction.

## Changes

- Added regression coverage for JSON artifact reads that include URL passwords, sensitive query values, bearer tokens, and structured `client_secret` values.
- Added regression coverage for Basic-auth artifact detail pages that include URL passwords, sensitive query values, cookies, and structured `api_key` values.
- Added recursive artifact payload redaction for `GET /artifacts/{artifact_id}`.
- Added recursive artifact payload redaction for `/admin/artifacts/{artifact_id}` HTML rendering.
- Preserved non-sensitive artifact values and existing HTML escaping while redacting secret-bearing keys and diagnostic strings.
- Documented that admin artifact payload responses are diagnostic views and that the artifact SHA-256 remains the provenance check for the unredacted stored payload.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_artifact_read_redacts_sensitive_payload_values tests/test_runtime.py::test_admin_console_artifact_view_redacts_sensitive_payload_values -q` - 2 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 292 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1527 passed, 93.97% coverage.
