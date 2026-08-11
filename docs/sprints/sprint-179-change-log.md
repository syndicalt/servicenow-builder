# Sprint 179 Change Log

## Scope

Production hardening: worker alert failure observability.

## Changes

- Added warning logs for failed worker-failure alert delivery.
- Added warning logs for failed stale-requeue alert delivery.
- Kept alert delivery best-effort: failures still increment `alert_failures` and do not crash the worker loop or mutate authoritative PostgreSQL job state.
- Redacted diagnostic text in worker alert failure logs so plain sensitive assignments such as `client_secret=value` and `access_token=value` are not emitted.
- Documented the worker alert failure logging posture in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_entrypoints.py::test_runtime_worker_run_loop_alert_failure_does_not_crash_worker_with_redacted_log -q` - 1 passed.
- `python3 -m pytest tests/test_runtime_worker_retention.py::test_run_loop_counts_stale_requeue_alert_delivery_failures -q` - 1 passed.
- `python3 -m pytest tests/test_runtime_entrypoints.py::test_runtime_worker_run_loop_alert_failure_does_not_crash_worker_with_redacted_log tests/test_runtime_worker_retention.py::test_run_loop_counts_stale_requeue_alert_delivery_failures -q` - 2 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 253 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1375 passed, 93.90% coverage.

## Residual Risk

- Alert delivery retry/backoff and escalation routing remain host owned. This sprint makes delivery failures observable without making the alert sink authoritative.
