# Sprint 776 Change Log - Compose explicit runtime roles

## Scope

Hardened local compose orchestration so API and worker services declare their runtime roles in
service environment configuration instead of relying only on image defaults.

## Tests First

- Added 2 failing-first compose runtime role assertions in
  `tests/test_container_runtime.py::test_compose_declares_runtime_roles_per_service`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_776_documents_compose_explicit_runtime_roles`.
- Initial failures proved `docker-compose.yml` did not declare `JEDI_RUNTIME_ROLE=api` or
  `JEDI_RUNTIME_ROLE=worker` at the service level, and this sprint log was absent.

## Changes

- Added `JEDI_RUNTIME_ROLE=api` to the compose `api` service environment.
- Added `JEDI_RUNTIME_ROLE=worker` to the compose `worker` service environment.
- Documented why compose intentionally duplicates the image-level role defaults.

## Verification

- Focused regression: `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "declares_runtime_roles_per_service or sprint_776"` -> 2 passed, 859 deselected.
- Static lint: `python3 -m ruff check src tests` -> passed.
- Static typing: `python3 -m mypy src tests` -> passed.
- Full coverage gate: `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` -> 3143 passed, 93.36% coverage.
