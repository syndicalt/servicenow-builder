# Sprint 803 Change Log - Executable runtime role boundaries

## Scope

Hardened runtime entrypoints so a process cannot start with a role that belongs to the other
executable surface.

## Tests First

- Added 2 failing-first runtime role entrypoint assertions in `tests/test_runtime_entrypoints.py`:
  - `test_runtime_api_build_app_rejects_worker_role_before_store_open`
  - `test_runtime_worker_run_once_rejects_api_role_before_processor_call`
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_803_documents_executable_runtime_role_boundaries`.
- Initial failures proved the API factory could accept `JEDI_RUNTIME_ROLE=worker` and the worker
  runner could accept `JEDI_RUNTIME_ROLE=api`.

## Changes

- `create_runtime_api()` now rejects `JEDI_RUNTIME_ROLE=worker` before settings validation opens the
  operational store or wires lifecycle and admin HTTP routes.
- `runtime_worker.run_once()` now rejects `JEDI_RUNTIME_ROLE=api` before invoking the fulfillment
  processor, including custom processors used in tests or operational wrappers.
- Documented that runtime role enforcement is an executable boundary, not only a Dockerfile or
  compose convention.

## Verification

- `python3 -m pytest tests/test_runtime_entrypoints.py -q -k "rejects_worker_role_before_store_open or rejects_api_role_before_processor_call or build_app_uses_env_file or run_once_delegates"`: 4 passed, 8 deselected.
- `python3 -m pytest tests/test_runtime_entrypoints.py -q`: 12 passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_803`: 1 passed, 875 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3199 passed, 93.36% coverage.
