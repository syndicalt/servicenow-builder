# Sprint 303 Change Log - Retention Numeric Settings Load Guard

## Summary

- Retention policy numeric settings now reject padded or control-character env values before integer parsing.
- `JEDI_RETENTION_ARTIFACT_BLOB_DAYS`, `JEDI_RETENTION_JOB_EVENT_DAYS`, and `JEDI_RETENTION_PRUNE_BATCH_SIZE` must be base-10 integers without padding or control characters.
- Empty values still mean retention is disabled or the default prune batch size is used, but whitespace-only values are rejected as padded operator input.
- Malformed retention numeric diagnostics name only the setting and do not echo padded or control-character fragments.
- Existing disabled-by-default, explicit-window, and non-positive retention validation remains intact.
- Added a failing regression proving padded retention numeric env values were previously accepted during retention policy loading.
- Documented the stricter retention numeric settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_operational_store.py -q -k "retention_policy"` - 1 test failed before implementation because padded retention numeric values were accepted during policy loading.
- `python3 -m pytest tests/test_operational_store.py -q -k "retention_policy"` - 5 passed after implementation.
- `python3 -m pytest tests/test_operational_store.py -q` - 38 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_three_documents_retention_numeric_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/operational_store.py tests/test_operational_store.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/operational_store.py tests/test_operational_store.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 377 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1817 passed, total coverage 93.90%.
