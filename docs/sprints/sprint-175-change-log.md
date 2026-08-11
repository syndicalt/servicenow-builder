# Sprint 175 Change Log

## Scope

Production hardening: opt-in stale-job recovery alert routing.

## Changes

- Added `stale_requeue_alert()` to convert actual stale-job recovery activity into strict `ExternalAlert` payloads.
- Extended `runtime_worker.run_loop()` with `stale_job_requeue_alert_emitter` support.
- Stale-job recovery alert delivery is best-effort and shares the existing `alerts_emitted` and `alert_failures` worker loop counters.
- Empty stale recovery sweeps do not emit external alerts.
- Wired `runtime_worker.main()` to emit stale-requeue alerts through `emit_alert_webhook()` only when stale recovery requeues one or more jobs and `JEDI_ALERT_WEBHOOK_ENABLED=true`.
- Documented that stale-requeue alerts are warning-severity operator signals and do not imply fulfillment success.

## Verification

- `python3 -m pytest tests/test_alert_delivery.py::test_stale_requeue_alert_summarizes_actual_requeued_jobs -q` - 1 passed.
- `python3 -m pytest tests/test_runtime_worker_retention.py::test_run_loop_emits_stale_requeue_alert_only_when_jobs_requeued tests/test_runtime_worker_retention.py::test_main_emits_stale_requeue_alert_when_recovery_requeues_jobs -q` - 2 passed.
- `python3 -m pytest tests/test_alert_delivery.py -q` - 6 passed.
- `python3 -m pytest tests/test_runtime_worker_retention.py -k "stale_requeue_alert or alert_webhook" -q` - 4 passed, 12 deselected.
- `python3 -m pytest tests/test_project_docs.py -q` - 249 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1360 passed, 93.88% coverage.

## Residual Risk

- Retention-prune and terminal rejected-job alerts still need explicit routing policy before external emission.
