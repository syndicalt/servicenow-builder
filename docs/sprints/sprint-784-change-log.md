# Sprint 784 Change Log - Compose read-only app roots

## Scope

Hardened local compose app containers so the API and worker run with read-only root filesystems while
retaining explicit writable paths for runtime artifacts and temporary files.

## Tests First

- Added 8 failing-first compose read-only root assertions in `tests/test_container_runtime.py::test_compose_uses_read_only_app_container_roots`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_784_documents_compose_read_only_app_roots`.
- Initial failures proved `docker-compose.yml` did not set `read_only: true`, did not mount `/tmp` as tmpfs, and this sprint log was absent.

## Changes

- Added `read_only: true` to the `api` and `worker` compose services.
- Added `/tmp` tmpfs mounts to the `api` and `worker` compose services for temporary-file compatibility.
- Preserved `runtime-artifacts:/app/artifacts` (`/app/artifacts`) as the explicit writable application artifact path.
- Documented the read-only app-container root posture in the operator guide.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "read_only_app_roots or read_only_app_container"`: 2 passed, 875 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3159 passed, total coverage 93.36%.
