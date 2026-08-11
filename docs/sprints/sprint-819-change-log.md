# Sprint 819 Change Log - Worker max-iteration ceiling validation

## Scope

Hardened configured worker loop bounds so `JEDI_WORKER_MAX_ITERATIONS` cannot be set so high that a
nominally bounded smoke or batch run behaves like an accidental long-running worker.

## Tests First

- Added 1 failing-first worker max-iteration assertion:
  `tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_excessive_max_iterations`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_819_documents_worker_max_iteration_ceiling`.
- Initial failure proved worker settings accepted a million configured iterations.

## Changes

- `JEDI_WORKER_MAX_ITERATIONS` now has a configured ceiling of `10000`.
- Leaving `JEDI_WORKER_MAX_ITERATIONS` unset remains the deliberate long-running worker mode.
- Diagnostics name the setting and ceiling without echoing the oversized configured value.
- Updated the operator guide to document the worker max-iteration ceiling.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "excessive_max_iterations or non_positive_max_iterations"`: 2 passed, 37 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_819`: 1 passed, 891 deselected.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q`: 39 passed.
- `python3 -m pytest tests/test_runtime.py -q`: 368 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3238 passed, 93.40% coverage.
