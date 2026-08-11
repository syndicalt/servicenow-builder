# Sprint 247 Change Log - Worker Idle Sleep Loop Hygiene

## Summary

- Worker idle sleep loop hygiene prevents unbounded workers from spinning continuously when the queue is idle.
- Added a worker settings regression test for `JEDI_WORKER_IDLE_SLEEP_SECONDS=0` without `JEDI_WORKER_MAX_ITERATIONS`.
- Updated `RuntimeWorkerSettings` so zero idle sleep remains valid for bounded smoke runs but fails for unbounded worker loops.
- Documented that unbounded workers must use a positive idle sleep interval to avoid a tight polling loop.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py::test_load_worker_settings_rejects_unbounded_zero_idle_sleep -q`
  - `1 passed`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `321 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1602 passed, 93.94% coverage`
