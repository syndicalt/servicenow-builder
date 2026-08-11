# Sprint 171 Change Log

## Scope

Production hardening: worker-safe stale running job recovery.

## Changes

- Added `PostgresOperationalStore.requeue_stale_running_jobs()` as the durable recovery primitive.
- The recovery SQL selects stale `running` jobs with `FOR UPDATE SKIP LOCKED`, updates them back to `queued`, clears `locked_by`, `locked_at`, and `last_error`, preserves `attempt_count`, and writes a `queued` `job_events` audit entry.
- Added `runtime_worker.requeue_stale_running_jobs()` to produce a structured recovery report with cutoff, count, and job ids.
- Added opt-in worker scheduler settings:
  - `JEDI_STALE_JOB_REQUEUE_ENABLED=false`
  - `JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS=3600`
  - `JEDI_STALE_JOB_REQUEUE_BATCH_SIZE=10`
- Wired the long-running worker to call stale recovery only when explicitly enabled.
- Documented the separation between read-only stale alerts and worker-side stale recovery in `docs/operator-guide.md`.

## Verification

- `python3 -m pytest tests/test_operational_store.py -k "requeue_stale_running_jobs" -q` - 2 passed, 35 deselected.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q` - 10 passed.
- `python3 -m pytest tests/test_operational_store.py -q` - 37 passed.
- `python3 -m pytest tests/test_runtime_worker_retention.py tests/test_operational_store.py -q` - 47 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 244 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1338 passed, 93.85% coverage.

## Residual Risk

- Recovery is intentionally opt-in. Operators still need a deployment policy for when stale requeue should be enabled.
- This sprint does not add distributed external alert delivery. It keeps stale recovery inside the authoritative worker/runtime boundary.
