# Sprint 174 Change Log

## Scope

Production hardening: opt-in worker failure alert emission.

## Changes

- Added `worker_failure_alert()` to convert failed `FulfillmentWorkerResult` records into strict `ExternalAlert` payloads.
- Added `alert_emitter` support to `runtime_worker.run_loop()`.
- Extended `RuntimeWorkerLoopSummary` with `alerts_emitted` and `alert_failures`.
- Worker alert delivery is best-effort. Delivery exceptions increment `alert_failures` and do not crash the worker loop or mutate PostgreSQL job state.
- Wired `runtime_worker.main()` to emit worker-failure alerts through `emit_alert_webhook()` only when `JEDI_ALERT_WEBHOOK_ENABLED=true` and `JEDI_ALERT_WEBHOOK_URL` is configured.
- Updated `UrllibTransport` to accept a configured timeout so `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS` is used by the worker alert transport.
- Documented that failed worker iterations emit external alerts when enabled, while successful, idle, stale-requeue, and retention-prune iterations do not emit external alerts yet.

## Verification

- `python3 -m pytest tests/test_runtime_entrypoints.py -k "alert" -q` - 2 passed, 6 deselected.
- `python3 -m pytest tests/test_alert_delivery.py -q` - 5 passed.
- `python3 -m pytest tests/test_runtime_worker_retention.py -k "alert_webhook" -q` - 1 passed, 12 deselected.
- `python3 -m pytest tests/test_servicenow.py -q` - 39 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 248 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1355 passed, 93.87% coverage.

## Residual Risk

- This sprint only emits failed worker iteration alerts. Stale-requeue summaries and terminal rejected-job alerts still need an explicit routing policy before external emission.
