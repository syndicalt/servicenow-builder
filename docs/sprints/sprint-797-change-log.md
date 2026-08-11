# Sprint 797 Change Log - Compose Postgres privilege reduction

## Scope

Hardened the local PostgreSQL operational-store container without breaking the official image's
startup and writable data-volume requirements.

## Tests First

- Added 5 failing-first compose Postgres privilege assertions in `tests/test_container_runtime.py::test_compose_reduces_postgres_container_privileges`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_797_documents_compose_postgres_privilege_reduction`.
- Initial failures proved the compose Postgres service did not declare `security_opt`, did not set `no-new-privileges:true`, did not bound process count, and this sprint log was absent.

## Changes

- Added `security_opt: no-new-privileges:true` to the compose Postgres service.
- Added `pids_limit: 512` to the compose Postgres service.
- Kept the Postgres root filesystem writable and avoided `cap_drop: ALL` because the official database image needs normal startup behavior and a writable data volume.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "postgres_container_privileges or postgres_privilege_reduction"`: 2 passed, 897 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3185 passed, 93.36% coverage.
