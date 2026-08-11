# Sprint 817 Change Log - Worker maintenance batch ceiling validation

## Scope

Hardened worker maintenance batch settings so retention pruning and stale-job requeue recovery cannot
be configured with unbounded batch sizes that create large lock or write bursts.

## Tests First

- Added 2 failing-first worker maintenance batch assertions:
  `tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_excessive_stale_requeue_batch_size`
  and
  `tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_excessive_retention_prune_batch_size`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_817_documents_worker_maintenance_batch_ceilings`.
- Initial failure proved worker settings accepted million-row maintenance batch sizes.

## Changes

- `JEDI_RETENTION_PRUNE_BATCH_SIZE` now has a ceiling of `5000`.
- `JEDI_STALE_JOB_REQUEUE_BATCH_SIZE` now has a ceiling of `100`.
- Diagnostics name the setting and ceiling without echoing the oversized configured value.
- Updated the operator guide to document the worker maintenance batch ceilings.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "excessive_stale_requeue_batch_size or excessive_retention_prune_batch_size or reads_retention_and_stale_requeue_environment"`: 3 passed, 34 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_817`: 1 passed, 889 deselected.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q`: 37 passed.
- `python3 -m pytest tests/test_runtime.py -q`: 368 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3234 passed, 93.39% coverage.
