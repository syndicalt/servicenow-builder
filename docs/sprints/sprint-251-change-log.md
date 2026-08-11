# Sprint 251 Change Log - Worker Boolean Parsing Hygiene

## Summary

- Worker boolean parsing hygiene prevents typoed worker environment values from silently changing operational behavior.
- Added a worker settings regression test for malformed values across `JEDI_WORKER_STOP_ON_FAILURE` and `JEDI_STALE_JOB_REQUEUE_ENABLED`.
- Replaced loose truthy parsing in `load_worker_settings()` with strict boolean parsing that accepts only `true`, `false`, `1`, `0`, `yes`, `no`, `on`, or `off`.
- Documented that malformed worker boolean values fail worker settings loading instead of being silently treated as false.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_malformed_worker_boolean_values tests/test_runtime_worker_retention.py::test_load_worker_settings_reads_retention_and_stale_requeue_environment tests/test_runtime_worker_retention.py::test_load_worker_settings_defaults_retention_disabled tests/test_runtime_worker_retention.py::test_main_wires_interval_gated_stale_job_recovery_when_enabled tests/test_runtime_worker_retention.py::test_main_wires_alert_webhook_emitter_when_enabled -q`
  - `5 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `325 passed`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1614 passed`
  - `Total coverage: 93.95%`
