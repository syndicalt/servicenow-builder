# Sprint 246 Change Log - Retention Prune Interval Hygiene

## Summary

- Retention prune interval hygiene prevents misconfiguration from creating continuous maintenance churn.
- Added a worker settings regression test for `JEDI_RETENTION_PRUNE_INTERVAL_SECONDS=0`.
- Updated `RuntimeWorkerSettings` so non-positive retention prune intervals fail settings loading.
- Documented that `JEDI_RETENTION_PRUNE_INTERVAL_SECONDS` must be greater than zero and cannot create a continuous retention maintenance loop.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_positive_retention_prune_interval -q`
  - `1 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `320 passed`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1600 passed, 93.94% coverage`
