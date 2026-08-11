# Sprint 172 Change Log

## Scope

Production hardening: fail-closed validation for stale job recovery worker settings.

## Changes

- Added worker settings validation for `JEDI_STALE_JOB_REQUEUE_BATCH_SIZE`.
- Added worker settings validation for `JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS`.
- Removed silent fallback behavior where `JEDI_STALE_JOB_REQUEUE_BATCH_SIZE=0` was treated as the default batch size.
- Kept `JEDI_WORKER_IDLE_SLEEP_SECONDS=0` valid for smoke tests and tight local loops; this sprint is scoped to stale recovery safety.
- Documented that invalid stale recovery values fail worker settings loading instead of being coerced to defaults.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py -k "non_positive_stale_requeue" -q` - 2 passed, 10 deselected.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q` - 12 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 245 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1341 passed, 93.86% coverage.

## Residual Risk

- This sprint does not add external alert delivery or incident routing. It closes a configuration correctness gap in the worker recovery path.
