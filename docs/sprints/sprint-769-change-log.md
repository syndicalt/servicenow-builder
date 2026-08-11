# Sprint 769 Change Log - Operational store schema readiness

## Scope

Made runtime readiness check the operational-store schema explicitly before reporting the API ready.
This catches reachable-but-uninitialized PostgreSQL deployments before lifecycle webhooks or admin
routes fail later during real work.

## Tests First

- Added 5 failing-first schema readiness assertions:
  - `tests/test_operational_store.py::test_verify_schema_ready_checks_required_operational_tables`
  - `tests/test_operational_store.py::test_verify_schema_ready_returns_false_when_required_table_is_missing`
  - `tests/test_runtime.py::test_runtime_readiness_checks_operational_store_without_auth`
  - `tests/test_runtime.py::test_runtime_readiness_fails_closed_without_secret_leakage`
  - `tests/test_runtime.py::test_runtime_readiness_reports_missing_schema_without_secret_leakage`
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_769_documents_operational_store_schema_readiness`
- Initial failures proved `verify_schema_ready()` did not exist, `/ready` still used a generic
  recent-event query, missing schema was not distinguishable, and this sprint log was absent.

## Changes

- Added `REQUIRED_OPERATIONAL_TABLES` for the packaged operational-store migrations.
- Added `PostgresOperationalStore.verify_schema_ready()` as a read-only information-schema probe.
- Added `RuntimeStore.verify_schema_ready()` to the shared API/worker store protocol.
- Updated `GET /ready` to:
  - call `verify_schema_ready()`.
  - return `200` with `operational_store=ok` when schema is present.
  - return `503` with `operational_store_schema=missing` when required tables are absent.
  - expose the missing-schema check name as `operational_store_schema`.
  - preserve the existing sanitized `operational_store=failed` response for exceptions.
- Documented operational store schema readiness in the operator guide.

## Verification

- `python3 -m pytest tests/test_operational_store.py tests/test_runtime.py tests/test_project_docs.py -q -k "verify_schema_ready or readiness or sprint_769"` - 13 passed, 1230 deselected.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3129 passed, 93.35% coverage.
