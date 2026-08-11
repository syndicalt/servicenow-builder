# Sprint 305 Change Log - Worker Boolean Settings Load Guard

## Summary

- Worker boolean settings loading now rejects padded or control-character env values before boolean normalization.
- `JEDI_WORKER_STOP_ON_FAILURE` and `JEDI_STALE_JOB_REQUEUE_ENABLED` must use accepted boolean literals without padding or control characters.
- Empty values still use each setting's default, but whitespace-only or padded values are rejected as ambiguous operator input.
- Malformed worker boolean diagnostics name only the setting and do not echo padded or control-character fragments.
- Existing accepted boolean literals and malformed-boolean validation remains intact.
- Added a failing regression proving padded worker boolean env values were previously accepted during worker settings loading.
- Documented the stricter worker boolean settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "worker_boolean_values or reads_retention_and_stale_requeue_environment"` - 1 test failed before implementation because padded worker boolean values were accepted during settings loading.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k "worker_boolean_values or reads_retention_and_stale_requeue_environment"` - 3 passed after implementation.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q` - 26 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_five_documents_worker_boolean_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_worker.py tests/test_runtime_worker_retention.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_worker.py tests/test_runtime_worker_retention.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 379 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1825 passed, total coverage 93.91%.
