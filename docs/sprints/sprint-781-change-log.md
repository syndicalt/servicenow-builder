# Sprint 781 Change Log - Compose API readiness healthcheck

## Scope

Added an API readiness healthcheck to local compose so operators can see PostgreSQL-backed runtime
readiness directly from container health state.

## Tests First

- Added 8 failing-first compose readiness assertions in `tests/test_container_runtime.py::test_compose_defines_api_readiness_healthcheck`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_781_documents_compose_api_readiness_healthcheck`.
- Initial failures proved `docker-compose.yml` only defined the Postgres healthcheck and this sprint log was absent.

## Changes

- Added an `api` service healthcheck in `docker-compose.yml` that calls `GET /ready` (`/ready`) on `127.0.0.1:8000`.
- Kept the Dockerfile healthcheck on `/health` as the cheap container liveness probe.
- Documented that `docker compose ps` now surfaces API readiness against the operational store.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "api_readiness_healthcheck or sprint_781"`: 2 passed, 869 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3153 passed, total coverage 93.36%.
