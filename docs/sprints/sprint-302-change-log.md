# Sprint 302 Change Log - Worker Numeric Settings Load Guard

## Summary

- Worker numeric settings loading now rejects padded or control-character env values before integer or float parsing.
- `JEDI_WORKER_MAX_ITERATIONS` and `JEDI_STALE_JOB_REQUEUE_BATCH_SIZE` must be base-10 integers without padding or control characters.
- `JEDI_WORKER_IDLE_SLEEP_SECONDS`, `JEDI_RETENTION_PRUNE_INTERVAL_SECONDS`, and `JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS` must be finite numbers without padding or control characters.
- Malformed worker numeric diagnostics name only the setting and do not echo padded or control-character fragments.
- Existing malformed numeric, non-finite float, and non-positive worker validation remains intact.
- Added a failing regression proving padded worker numeric env values were previously accepted during worker settings loading.
- Documented the stricter worker numeric settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "worker_numeric_values or non_finite_worker_float_values or reads_retention_and_stale_requeue_environment"` - 1 test failed before implementation because padded worker numeric values were accepted during settings loading.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "worker_numeric_values or non_finite_worker_float_values or reads_retention_and_stale_requeue_environment"` - 4 passed after implementation.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q` - 25 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_two_documents_worker_numeric_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_worker.py tests/test_runtime_worker_retention.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_worker.py tests/test_runtime_worker_retention.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 376 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1815 passed, total coverage 93.91%.
