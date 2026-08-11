# Sprint 256 Change Log - Non-Finite Float Settings Guard

## Summary

- Non-finite float settings guarding prevents `nan`, `inf`, and `-inf` from reaching runtime timeouts, worker sleeps, retention pruning intervals, or stale-job recovery intervals.
- Added runtime settings regressions for non-finite `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS` and `JEDI_PUBLIC_WEB_TIMEOUT_SECONDS` values.
- Added worker settings regressions for non-finite `JEDI_WORKER_IDLE_SLEEP_SECONDS`, `JEDI_RETENTION_PRUNE_INTERVAL_SECONDS`, and `JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS` values.
- Updated runtime and worker float parsers to raise setting-specific errors when parsed values are not finite.
- Documented finite-number requirements for runtime and worker float environment values.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_non_finite_runtime_float_values tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_runtime_float_values tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_finite_worker_float_values tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_malformed_worker_numeric_values tests/test_runtime_worker_retention.py::test_load_worker_settings_reads_retention_and_stale_requeue_environment -q` - 7 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_worker.py tests/test_runtime.py tests/test_runtime_worker_retention.py` - all checks passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success with 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 330 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1643 passed with 93.97% total coverage.
