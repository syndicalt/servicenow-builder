# Sprint 428 Change Log

## Worker optional-float parser safe exceptions

Hardened worker-only decimal setting parsing so unstringifiable parser exceptions cannot replace controlled worker startup diagnostics. Prior behavior caught decimal parser `ValueError`s in `runtime_worker._optional_float()`, then called `str(exc)` directly while wrapping the parser failure.

The worker config path now formats those failures through `exception_diagnostic_message(..., fallback_subject="runtime worker")`. Normal parser diagnostics are preserved as before. If a parser dependency or future validator raises an exception that cannot be stringified, worker settings loading fails with `runtime worker raised unstringifiable <ExceptionType>` or the generic `runtime worker raised unstringifiable exception` instead of leaking a secondary stringification error.

This covers worker-only decimal controls such as `JEDI_WORKER_IDLE_SLEEP_SECONDS`, `JEDI_RETENTION_PRUNE_INTERVAL_SECONDS`, and `JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS`, keeping the worker loop's startup diagnostics aligned with runtime config, handler, lifecycle, CLI, and fulfillment-worker exception hardening.

## Verification

- Added 1 failing-first worker settings test covering an unstringifiable decimal parser failure.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "worker_optional_float_wraps_unstringifiable_parser_errors"`: failed before implementation because `client-secret-value` escaped during worker decimal parser error wrapping.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "worker_optional_float_wraps_unstringifiable_parser_errors"`: 1 test passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 502 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2275 total tests passed at 93.97% coverage.
