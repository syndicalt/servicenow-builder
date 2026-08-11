# Sprint 818 Change Log - Worker scheduler interval ceiling validation

## Scope

Hardened worker scheduler interval settings so fulfillment polling, retention pruning, and stale-job
recovery cannot be configured with multi-day delays.

## Tests First

- Added 1 failing-first worker scheduler interval assertion:
  `tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_excessive_worker_scheduler_intervals`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_818_documents_worker_scheduler_interval_ceilings`.
- Initial failure proved worker settings accepted week-long maintenance intervals and one-hour idle
  polling sleeps.

## Changes

- `JEDI_WORKER_IDLE_SLEEP_SECONDS` now has a ceiling of `300`.
- `JEDI_RETENTION_PRUNE_INTERVAL_SECONDS` now has a ceiling of `86400`.
- `JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS` now has a ceiling of `86400`.
- Diagnostics name the setting and ceiling without echoing the oversized configured value.
- Updated the operator guide to document the worker scheduler interval ceilings.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "excessive_worker_scheduler_intervals or non_positive_stale_requeue_interval or non_positive_retention_prune_interval or unbounded_zero_idle_sleep"`: 4 passed, 34 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_818`: 1 passed, 890 deselected.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q`: 38 passed.
- `python3 -m pytest tests/test_runtime.py -q`: 368 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3236 passed, 93.40% coverage.
