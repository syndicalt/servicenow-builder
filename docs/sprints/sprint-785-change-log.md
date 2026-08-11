# Sprint 785 Change Log - Compose worker API readiness dependency

## Scope

Hardened local compose startup ordering so the worker waits for both Postgres and API readiness before
starting fulfillment work.

## Tests First

- Added 5 failing-first compose dependency assertions in `tests/test_container_runtime.py::test_compose_worker_waits_for_api_readiness`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_785_documents_compose_worker_api_readiness_dependency`.
- Initial failures proved the worker depended only on Postgres `condition: service_healthy` and this sprint log was absent.

## Changes

- Added an `api` `condition: service_healthy` dependency to the worker compose service.
- Preserved the existing Postgres `condition: service_healthy` dependency.
- Documented that worker startup now waits for `api` readiness and operational-store reachability.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "worker_api_readiness_dependency or worker_waits_for_api"`: 2 passed, 877 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3161 passed, total coverage 93.36%.
