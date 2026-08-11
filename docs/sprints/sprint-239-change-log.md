# Sprint 239 Change Log - PostgreSQL Operational Store URL Fragment Hygiene

## Summary

- PostgreSQL operational store URL fragment hygiene closes an ambiguity in production database configuration.
- Added a production startup regression test for `DATABASE_URL` values that include URL fragments.
- Updated runtime validation so production deployments reject PostgreSQL URLs with fragments before the API or worker starts.
- Documented that the production operational store URL must be PostgreSQL-only and must not include URL fragments.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_production_database_url_fragments -q`
  - `1 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `313 passed`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1586 passed, 93.92% coverage`
