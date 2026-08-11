# Sprint 775 Change Log - Compose role-specific runtime images

## Scope

Hardened the local compose runtime so the API and worker services build from their role-specific
Dockerfiles instead of letting the worker inherit the API image defaults.

## Tests First

- Added 2 failing-first compose Dockerfile assertions in
  `tests/test_container_runtime.py::test_compose_uses_role_specific_runtime_dockerfiles`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_775_documents_compose_role_specific_images`.
- Initial failures proved `docker-compose.yml` built both runtime services from the default
  Dockerfile and this sprint log was absent.

## Changes

- Changed the compose `api` service to build with `dockerfile: Dockerfile`.
- Changed the compose `worker` service to build with `dockerfile: Dockerfile.worker` from
  `Dockerfile.worker`, preserving the image-level `JEDI_RUNTIME_ROLE=worker` default.
- Preserved local restart policy assertions while making them independent of compose build stanza
  formatting.
- Documented the compose runtime-role image boundary in the operator guide.

## Verification

- Focused regression: `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "role_specific_runtime_dockerfiles or restart_policies or sprint_775"` -> 4 passed, 855 deselected.
- Static lint: `python3 -m ruff check src tests` -> passed.
- Static typing: `python3 -m mypy src tests` -> passed.
- Full coverage gate: `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` -> 3141 passed, 93.36% coverage.
