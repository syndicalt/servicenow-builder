# Sprint 180 Change Log

## Scope

Production hardening: worker maintenance failure isolation.

## Changes

- Isolated periodic retention prune failures from normal fulfillment processing.
- Isolated periodic stale running job recovery failures from normal fulfillment processing.
- Added `prune_failures` and `stale_job_recovery_failures` to `RuntimeWorkerLoopSummary`.
- Added redacted warning logs for prune and stale recovery failures.
- Preserved existing interval behavior after both successful and failed maintenance attempts.
- Documented that maintenance failures do not crash the worker loop or mutate PostgreSQL job state unless the maintenance operation completed its own transaction.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py::test_run_loop_logs_pruner_failure_and_continues_processing tests/test_runtime_worker_retention.py::test_run_loop_logs_stale_recovery_failure_and_continues_processing -q` - 2 passed.
- `python3 -m pytest tests/test_runtime_worker_retention.py::test_run_loop_invokes_pruner_only_when_interval_elapses tests/test_runtime_worker_retention.py::test_run_loop_invokes_stale_job_recoverer_only_when_interval_elapses -q` - 2 passed.
- `python3 -m pytest tests/test_runtime_worker_retention.py::test_run_loop_logs_pruner_failure_and_continues_processing tests/test_runtime_worker_retention.py::test_run_loop_logs_stale_recovery_failure_and_continues_processing tests/test_runtime_worker_retention.py::test_run_loop_invokes_pruner_only_when_interval_elapses tests/test_runtime_worker_retention.py::test_run_loop_invokes_stale_job_recoverer_only_when_interval_elapses -q` - 4 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 254 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1378 passed, 93.90% coverage.

## Residual Risk

- Repeated maintenance failures still need host-level alerting policy. This sprint makes them visible in logs and loop summaries without making maintenance authoritative over fulfillment.
