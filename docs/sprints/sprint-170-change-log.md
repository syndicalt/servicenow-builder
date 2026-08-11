# Sprint 170 Change Log

## Scope

Production hardening: stale running job detection for operational alerts.

## Changes

- Added `JEDI_RUNNING_JOB_STALE_AFTER_SECONDS` with a default of `3600` seconds.
- Added production validation requiring the stale-running threshold to be positive.
- Extended `GET /admin/alerts` to include stale running jobs alongside failed and rejected fulfillment jobs.
- Kept stale running job detection non-mutating. The admin API does not fail, retry, unlock, or requeue stale work because a worker may still own the job.
- Added admin console rendering for stale running job alerts.
- Documented operator guidance in `docs/operator-guide.md`, including the drill-down path to job events, ServiceNow work notes, and worker logs.

## Verification

- `python3 -m pytest tests/test_runtime.py -k "stale" -q` - 4 passed, 72 deselected.
- `python3 -m pytest tests/test_runtime.py -q` - 76 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 242 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1331 passed, 93.83% coverage.

## Residual Risk

- This sprint does not implement automated recovery for stale jobs. Recovery needs a separate worker-safe lease/retry design with idempotency and ServiceNow writeback guarantees.
- This sprint does not emit alerts to external systems. It keeps the operator-facing projection ready for later delivery channels.
