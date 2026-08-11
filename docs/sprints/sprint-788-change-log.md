# Sprint 788 Change Log - Compose app PID limits

## Scope

Added app-container PID limits to local compose so API and worker fault scenarios cannot create
unbounded process-count pressure on the host during hardening or lifecycle replay runs.

## Tests First

- Added 5 failing-first compose PID assertions in `tests/test_container_runtime.py::test_compose_limits_app_container_process_counts`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_788_documents_compose_app_pid_limits`.
- Initial failures proved `docker-compose.yml` did not set `pids_limit: 256` for app services and this sprint log was absent.

## Changes

- Added `pids_limit: 256` to the `api` compose service.
- Added `pids_limit: 256` to the `worker` compose service.
- Documented the app-container process-count exhaustion boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "app_pid_limits or process_counts"`: 2 passed, 883 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3167 passed, total coverage 93.36%.
