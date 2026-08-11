# Sprint 253 Change Log - Worker Numeric Parsing Hygiene

## Summary

- Worker numeric parsing hygiene prevents malformed worker environment values from surfacing raw parser errors or losing the setting name.
- Added a worker settings regression test for malformed integer values across `JEDI_WORKER_MAX_ITERATIONS` and `JEDI_STALE_JOB_REQUEUE_BATCH_SIZE`.
- Added a worker settings regression test for malformed numeric values across `JEDI_WORKER_IDLE_SLEEP_SECONDS`, `JEDI_RETENTION_PRUNE_INTERVAL_SECONDS`, and `JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS`.
- Updated `load_worker_settings()` numeric parsers so malformed values raise setting-specific errors with the expected numeric type.
- Documented that malformed worker numeric values fail worker settings loading with stable diagnostics.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_malformed_worker_numeric_values tests/test_runtime_worker_retention.py::test_load_worker_settings_reads_retention_and_stale_requeue_environment tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_positive_stale_requeue_interval tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_positive_retention_prune_interval tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_positive_max_iterations -q`
  - `5 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `327 passed`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1632 passed`
  - `Total coverage: 93.95%`
