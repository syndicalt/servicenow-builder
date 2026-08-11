# Sprint 783 Change Log - Compose runtime privilege reduction

## Scope

Reduced local compose privileges for the JEDI API and worker application containers without changing
the Postgres container runtime posture.

## Tests First

- Added 8 failing-first compose privilege assertions in `tests/test_container_runtime.py::test_compose_reduces_api_and_worker_container_privileges`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_783_documents_compose_runtime_privilege_reduction`.
- Initial failures proved `docker-compose.yml` had no `security_opt` or `cap_drop` declarations for app containers and this sprint log was absent.

## Changes

- Added `security_opt` with `no-new-privileges:true` to the `api` and `worker` compose services.
- Added `cap_drop: [ALL]` behavior to the `api` and `worker` compose services using YAML list form.
- Documented that this is app-container privilege hardening layered on top of the non-root image user.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "privilege_reduction or reduces_api_and_worker"`: 2 passed, 873 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3157 passed, total coverage 93.36%.
