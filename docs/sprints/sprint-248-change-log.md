# Sprint 248 Change Log - Worker Max Iteration Hygiene

## Summary

- Worker max iteration hygiene prevents bounded workers from being configured to silently start and exit without processing.
- Added a worker settings regression test for `JEDI_WORKER_MAX_ITERATIONS=0`.
- Updated `RuntimeWorkerSettings` so configured max-iteration values must be greater than zero.
- Documented that leaving `JEDI_WORKER_MAX_ITERATIONS` unset creates an unbounded worker, while configured values must be positive.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_positive_max_iterations -q`
  - `1 passed`
- `python3 -m pytest tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_non_positive_max_iterations tests/test_runtime_entrypoints.py::test_runtime_worker_load_worker_settings_reads_loop_environment -q`
  - `2 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `322 passed`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1604 passed`
  - `Total coverage: 93.94%`
