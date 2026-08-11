# Sprint 774 Change Log - Compose runtime restart policies

## Scope

Hardened the local compose runtime so operator smoke runs and local development stacks have explicit
restart behavior instead of relying on Docker defaults.

## Tests First

- Added 3 failing-first compose restart assertions in
  `tests/test_container_runtime.py::test_compose_defines_runtime_restart_policies`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_774_documents_compose_runtime_restart_policies`.
- Initial failures proved `docker-compose.yml` had no restart policies and this sprint log was
  absent.

## Changes

- Added `restart: unless-stopped` to the `postgres` service.
- Added `restart: on-failure` to the `api` service.
- Added `restart: on-failure` to the `worker` service.
- Documented local compose restart policies in the operator guide.

## Verification

- Focused regression: `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "restart_policies or sprint_774"` -> 2 passed, 855 deselected.
- Static lint: `python3 -m ruff check src tests` -> passed.
- Static typing: `python3 -m mypy src tests` -> passed.
- Full coverage gate: `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` -> 3139 passed, 93.36% coverage.
