# Sprint 798 Change Log - Compose Postgres graceful shutdown

## Scope

Hardened local operational-store reliability by giving the compose PostgreSQL service an explicit
database shutdown signal and grace period.

## Tests First

- Added 3 failing-first compose Postgres graceful shutdown assertions in `tests/test_container_runtime.py::test_compose_defines_postgres_graceful_shutdown_window`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_798_documents_compose_postgres_graceful_shutdown`.
- Initial failures proved the compose Postgres service did not define `stop_signal`, did not define a database-specific `stop_grace_period`, and this sprint log was absent.

## Changes

- Added `stop_signal: SIGTERM` to the compose Postgres service.
- Added `stop_grace_period: 60s` to the compose Postgres service.
- Documented that the database gets a longer explicit shutdown window than the app containers.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "postgres_graceful_shutdown"`: 2 passed, 899 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3187 passed, 93.36% coverage.
