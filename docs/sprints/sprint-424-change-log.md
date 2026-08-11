# Sprint 424 Change Log

## Runtime-worker logging-safe exception formatting

Hardened best-effort runtime-worker logging paths so maintenance and alert failures cannot break the worker loop while being logged. Prior behavior caught retention prune, stale-job recovery, stale-requeue alert, and worker failure-alert exceptions, but then called `str(error)` in the logger arguments. If stringification itself failed, the logging path could re-raise and prevent the loop from reaching the normal processor, failure counters, or stop-policy handling.

The runtime worker now formats these exceptions through a safe diagnostic helper before redaction. Normal exception messages are preserved and redacted as before. Unstringifiable exceptions are logged as `runtime worker raised unstringifiable <ExceptionType>` when the type label is safe, or `runtime worker raised unstringifiable exception` when the type label is unsafe, non-ASCII, oversized, or mutated.

This keeps retention pruning, stale-job recovery, stale-requeue alerting, and worker failure-alert delivery isolated as best-effort operational paths.

## Verification

- Added 4 failing-first tests covering unstringifiable retention prune, stale-job recovery, stale-requeue alert, and worker failure-alert exceptions.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "unstringifiable"`: failed before implementation because `ValueError: client-secret-value` escaped all four logging paths.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q`: 32 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 191 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 498 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2262 total tests passed at 93.93% coverage.
