# Sprint 832 Change Log - Stale requeue direct-control guard

## Scope

Hardened the direct stale-job requeue primitive so embedded callers cannot bypass worker settings and mutate PostgreSQL with unsafe stale thresholds or batch sizes.

## Tests First

- Added 1 failing-first stale requeue control assertion: `tests/test_runtime_worker_retention.py::test_requeue_stale_running_jobs_rejects_invalid_controls_before_store_open`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_832_documents_stale_requeue_direct_control_guard`.
- Initial failure proved `requeue_stale_running_jobs()` accepted unsafe stale thresholds and batch sizes, opened the operational store before validation, and surfaced raw `TypeError` for string stale thresholds.

## Changes

- `requeue_stale_running_jobs()` now validates `JEDI_RUNNING_JOB_STALE_AFTER_SECONDS` and `JEDI_STALE_JOB_REQUEUE_BATCH_SIZE` shaped direct inputs before stale cutoff calculation or store access.
- Direct stale requeue validation rejects non-positive values, booleans, non-integers, thresholds above 86400 seconds, and batch sizes above 100.
- Invalid direct controls fail before PostgreSQL mutation, runtime report output, or store factory invocation.
- Updated the operator guide to document the direct stale requeue control boundary.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "requeue_stale_running_jobs_rejects_invalid_controls_before_store_open or requeue_stale_running_jobs_uses_store_factory"` - 11 passed, 50 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_832` - 1 passed, 904 deselected.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q` - 61 passed.
- `python3 -m pytest tests/test_runtime.py -q` - 399 passed.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 202 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3308 passed, 93.40% coverage.
