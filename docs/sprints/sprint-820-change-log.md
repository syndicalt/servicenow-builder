# Sprint 820 Change Log - Production worker stop-on-failure rejection

## Scope

Hardened hosted worker reliability so production workers cannot be configured to exit after the first
failed fulfillment job.

## Tests First

- Added 1 failing-first production stop-on-failure assertion:
  `tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_stop_on_failure_in_production`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_820_documents_production_stop_on_failure_rejection`.
- Initial failure proved production worker settings accepted `JEDI_WORKER_STOP_ON_FAILURE=true`.

## Changes

- `JEDI_WORKER_STOP_ON_FAILURE` remains a development and smoke-test control.
- `JEDI_WORKER_STOP_ON_FAILURE=true` is now rejected when `JEDI_ENVIRONMENT=production`.
- Development and bounded smoke-test usage remains available outside production.
- Updated the operator guide to document the production stop-on-failure rejection.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "stop_on_failure_in_production or reads_retention_and_stale_requeue_environment"`: 2 passed, 38 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_820`: 1 passed, 892 deselected.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q`: 40 passed.
- `python3 -m pytest tests/test_runtime.py -q`: 368 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3240 passed, 93.40% coverage.
