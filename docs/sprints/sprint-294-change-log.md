# Sprint 294 Change Log - Worker ID Settings Load Guard

## Summary

- Runtime settings loading now rejects malformed `JEDI_WORKER_ID` env values.
- Worker ids must be non-empty, unpadded, and free of control characters before they enter worker settings.
- The default worker id remains `jedi-devproject-worker` when `JEDI_WORKER_ID` is absent.
- Existing production validation for direct `RuntimeSettings.worker_id` values remains intact.
- Added failing regressions proving padded and control-character worker id env values were previously accepted during settings loading.
- Documented the worker id settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k malformed_worker_id` - 3 tests failed before implementation because malformed worker id env values were accepted during settings loading.
- `python3 -m pytest tests/test_runtime.py -q -k malformed_worker_id` - 4 passed after implementation.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_ninety_four_documents_worker_id_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 368 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1781 passed, total coverage 93.92%.
