# Sprint 831 Change Log - Worker loop direct-control guard

## Scope

Hardened the direct worker loop primitive so embedded callers cannot bypass validated worker settings and start unsafe loops.

## Tests First

- Added 1 failing-first worker loop control assertion: `tests/test_runtime_worker_retention.py::test_run_loop_rejects_invalid_controls_before_processing`.
- Added 1 failing-first production stop-on-failure assertion: `tests/test_runtime_worker_retention.py::test_run_loop_rejects_stop_on_failure_in_production_before_processing`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_831_documents_worker_loop_control_guard`.
- Initial failure proved direct `run_loop()` accepted invalid max-iteration settings and could enter an unbounded zero-sleep loop before rejecting unsafe controls.

## Changes

- `run_loop()` now validates direct controls before the worker processor, pruner, stale-job recoverer, alert emitter, or sleep function runs.
- Direct worker-loop validation rejects non-positive or oversized `JEDI_WORKER_MAX_ITERATIONS`, unbounded zero `JEDI_WORKER_IDLE_SLEEP_SECONDS`, non-finite or oversized sleep values, non-positive or oversized maintenance intervals, and `JEDI_WORKER_STOP_ON_FAILURE` set to true in production.
- Bounded smoke loops can still use `idle_sleep_seconds=0` when `max_iterations` is configured.
- Updated the operator guide to document the direct `run_loop()` control boundary.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "run_loop_rejects_invalid_controls_before_processing or run_loop_rejects_stop_on_failure"` - 11 passed, 40 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_831` - 1 passed, 903 deselected.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q` - 51 passed.
- `python3 -m pytest tests/test_runtime.py -q` - 399 passed.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 202 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3297 passed, 93.39% coverage.
