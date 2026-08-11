# Sprint 787 Change Log - Compose app init shim

## Scope

Added Docker's init shim to local compose app services so API and worker containers handle PID 1
signal forwarding and child-process reaping consistently during local hardening runs.

## Tests First

- Added 5 failing-first compose init assertions in `tests/test_container_runtime.py::test_compose_app_services_use_init_shim`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_787_documents_compose_app_init_shim`.
- Initial failures proved `docker-compose.yml` did not set `init: true` for app services and this sprint log was absent.

## Changes

- Added `init: true` to the `api` compose service.
- Added `init: true` to the `worker` compose service.
- Documented the signal forwarding and child-process reaping boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "app_init_shim or app_services_use_init"`: 2 passed, 881 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3165 passed, total coverage 93.36%.
