# Sprint 789 Change Log - Compose app graceful shutdown

## Scope

Made local compose shutdown behavior explicit for the API and worker app services so runtime stop
semantics are visible and bounded during operational hardening runs.

## Tests First

- Added 6 failing-first compose graceful shutdown assertions in `tests/test_container_runtime.py::test_compose_defines_app_graceful_shutdown_window`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_789_documents_compose_app_graceful_shutdown`.
- Initial failures proved `docker-compose.yml` did not set explicit app service stop signals or grace periods and this sprint log was absent.

## Changes

- Added `stop_signal: SIGTERM` to the `api` and `worker` compose services.
- Added `stop_grace_period: 30s` to the `api` and `worker` compose services.
- Documented the bounded graceful shutdown window in the operator guide.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "app_graceful_shutdown or graceful_shutdown_window"`: 2 passed, 885 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3169 passed, total coverage 93.36%.
