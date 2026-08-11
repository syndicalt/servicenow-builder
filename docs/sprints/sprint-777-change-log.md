# Sprint 777 Change Log - Compose Postgres password externalization

## Scope

Hardened the local compose runtime so the PostgreSQL password is supplied by operator environment
configuration instead of being hardcoded in `docker-compose.yml`.

## Tests First

- Added 4 failing-first compose credential assertions:
  - `tests/test_container_runtime.py::test_compose_defines_api_worker_and_postgres_services`
  - `tests/test_container_runtime.py::test_compose_externalizes_postgres_password`
  - `tests/test_project_docs.py::test_sprint_777_documents_compose_postgres_password_externalization`
- Initial failures proved `POSTGRES_PASSWORD: jedi`, `postgresql://jedi:jedi@postgres:5432/jedi`,
  and this sprint log were still present or missing in the relevant contracts.

## Changes

- Replaced the hardcoded compose `POSTGRES_PASSWORD` value with
  `JEDI_POSTGRES_PASSWORD`.
- Updated API and worker compose `DATABASE_URL` values to use the same
  `JEDI_POSTGRES_PASSWORD` variable.
- Documented the required local compose password variable in the operator guide.

## Verification

- Focused regression: `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "externalizes_postgres_password or compose_defines_api_worker or sprint_777"` -> 3 passed, 860 deselected.
- Static lint: `python3 -m ruff check src tests` -> passed.
- Static typing: `python3 -m mypy src tests` -> passed.
- Full coverage gate: `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` -> 3145 passed, 93.36% coverage.
