# Sprint 778 Change Log - Compose password example config

## Scope

Updated example configuration so the local compose PostgreSQL password requirement is discoverable
without normalizing a shared default credential.

## Tests First

- Added 3 failing-first env example assertions in
  `tests/test_container_runtime.py::test_env_example_documents_compose_postgres_password_without_default`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_778_documents_compose_password_example_config`.
- Initial failures proved `.env.example` did not include `JEDI_POSTGRES_PASSWORD=` and this sprint
  log was absent.

## Changes

- Added an empty `JEDI_POSTGRES_PASSWORD=` placeholder to `.env.example`.
- Documented that the placeholder is required for local compose and intentionally has no default.
- Documented the example configuration behavior in the operator guide.

## Verification

- Focused regression: `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "env_example_documents_compose_postgres_password or sprint_778"` -> 2 passed, 863 deselected.
- Static lint: `python3 -m ruff check src tests` -> passed.
- Static typing: `python3 -m mypy src tests` -> passed.
- Full coverage gate: `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` -> 3147 passed, 93.36% coverage.
