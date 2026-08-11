# Sprint 786 Change Log - Compose bounded service logs

## Scope

Added bounded Docker log rotation to local compose services so repeated lifecycle and UAT runs cannot
grow service logs without limit.

## Tests First

- Added 7 failing-first compose logging assertions in `tests/test_container_runtime.py::test_compose_bounds_service_log_files`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_786_documents_compose_bounded_service_logs`.
- Initial failures proved `docker-compose.yml` had no service-level `logging` blocks and this sprint log was absent.

## Changes

- Added Docker `json-file` logging to `postgres`, `api`, and `worker`.
- Set `max-size: "10m"` and `max-file: "5"` for each service.
- Documented the local log-growth boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "bounded_service_logs or bounds_service_log"`: 2 passed, 879 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3163 passed, total coverage 93.36%.
