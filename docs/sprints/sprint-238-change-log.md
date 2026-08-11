# Sprint 238 Change Log

Scope: Production hardening - PostgreSQL operational store URL enforcement.

## Changes

- Added regression coverage that production validation rejects non-PostgreSQL `DATABASE_URL` values.
- Added production runtime validation for the operational store URL.
- `DATABASE_URL` must use a PostgreSQL scheme and must not include raw or encoded whitespace or control characters in production.
- Documented the production PostgreSQL operational-store URL rule in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_non_postgres_production_database_url -q` - 1 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 312 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1584 passed, 93.92% coverage.
