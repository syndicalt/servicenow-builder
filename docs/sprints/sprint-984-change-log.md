# Sprint 984 Change Log - Writeback orchestration story fetch guard

## Summary

Hardened writeback story-fetch handling so malformed ServiceNow story collections cannot execute truthiness, indexing, or model hooks before verification, writeback planning, build-claim planning, required-field validation, or story mutation.

`verify_writeback()`, `execute_writeback()`, and `execute_build_claim()` now route `fetch_stories()` results through `_writeback_stories()`. The helper accepts only exact Python lists containing exact `Story` records and fails closed with `writeback stories contain non-JSON value`.

## Security impact

- Malformed story collections fail before truthiness hooks, story-not-found handling, indexing, state checks, verification comparison, writeback planning, story mutation, audit writing, or batch report construction.
- Malformed story items fail before model-subclass hooks can run.
- Diagnostics do not include collection type names, item type names, hook output, or credential-like fragments.
- Writeback execution and build-claim execution fail before ServiceNow mutation and before audit artifacts are written.

## Tests

- Added 1 failing-first writeback verification story collection assertion: `test_verify_writeback_rejects_story_collection_subclass_without_leak`.
- Added 1 writeback execution story item assertion: `test_execute_writeback_rejects_story_item_subclass_before_mutation`.
- Added 1 build-claim execution story collection assertion: `test_execute_build_claim_rejects_story_collection_subclass_before_mutation`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_984_documents_writeback_orchestration_story_fetch_guard`.

## Verification

- `pytest tests/test_writeback_orchestration.py::test_verify_writeback_rejects_story_collection_subclass_without_leak tests/test_writeback_orchestration.py::test_execute_writeback_rejects_story_item_subclass_before_mutation tests/test_writeback_orchestration.py::test_execute_build_claim_rejects_story_collection_subclass_before_mutation -q` failed before implementation because malformed story data executed collection truthiness and model-copy hooks.
- `pytest tests/test_writeback_orchestration.py::test_verify_writeback_rejects_story_collection_subclass_without_leak tests/test_writeback_orchestration.py::test_execute_writeback_rejects_story_item_subclass_before_mutation tests/test_writeback_orchestration.py::test_execute_build_claim_rejects_story_collection_subclass_before_mutation tests/test_project_docs.py::test_sprint_984_documents_writeback_orchestration_story_fetch_guard -q` - 4 passed.
- `pytest tests/test_writeback_orchestration.py -q` - 38 passed.
- `pytest tests/test_project_docs.py -q` - 1057 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3709 passed, 93.27% coverage.
