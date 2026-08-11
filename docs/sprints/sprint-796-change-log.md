# Sprint 796 Change Log - Compose Postgres image digest pinning

## Scope

Hardened local compose supply-chain posture by pinning the PostgreSQL operational-store image to the
current immutable multi-architecture image digest instead of relying on the mutable `postgres:16`
tag alone.

## Tests First

- Added 3 failing-first compose Postgres digest assertions in `tests/test_container_runtime.py::test_compose_pins_postgres_image_digest`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_796_documents_compose_postgres_digest_pinning`.
- Initial failures proved `docker-compose.yml` still used unpinned `postgres:16` and this sprint log was absent.

## Changes

- Replaced the compose Postgres image declaration with `postgres:16@sha256:95206741a5b214807675e14165369d05b93a9cf692223b616d07cca227e74b0b`.
- Documented that Postgres image digest refreshes are intentional database base-image maintenance work after upstream image review and local compose validation.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "pins_postgres_image_digest or compose_postgres_digest"`: 2 passed, 895 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3183 passed, 93.36% coverage.
