# Sprint 983 Change Log - Writeback orchestration dictionary field guard

## Summary

Hardened external-build and build-claim writeback dictionary metadata handling so malformed ServiceNow dictionary-field collections cannot execute iteration or model hooks before capability decisions, required-field validation, or story mutation.

`evaluate_writeback_capability()`, `execute_writeback()`, and `execute_build_claim()` now route `fetch_story_dictionary_fields()` results through `_writeback_dictionary_fields()`. The helper accepts only exact Python lists containing exact `StoryDictionaryField` records and fails closed with `writeback dictionary fields contain non-JSON value`.

## Security impact

- Malformed dictionary-field collections fail before iteration hooks, field extraction, required-field validation, capability decisions, story mutation, audit writing, or batch report construction.
- Malformed dictionary-field items fail before model-subclass hooks can run.
- Diagnostics do not include collection type names, item type names, hook output, or credential-like fragments.
- Writeback execution fails before ServiceNow mutation and before audit artifacts are written.

## Tests

- Added 1 failing-first writeback capability dictionary-field collection assertion: `test_evaluate_writeback_capability_rejects_dictionary_field_collection_subclass_without_leak`.
- Added 1 writeback capability dictionary-field item assertion: `test_evaluate_writeback_capability_rejects_dictionary_field_item_subclass_without_leak`.
- Added 1 writeback execution mutation-boundary assertion: `test_execute_writeback_rejects_dictionary_field_collection_subclass_before_mutation`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_983_documents_writeback_orchestration_dictionary_field_guard`.

## Verification

- `pytest tests/test_writeback_orchestration.py::test_evaluate_writeback_capability_rejects_dictionary_field_collection_subclass_without_leak tests/test_writeback_orchestration.py::test_evaluate_writeback_capability_rejects_dictionary_field_item_subclass_without_leak tests/test_writeback_orchestration.py::test_execute_writeback_rejects_dictionary_field_collection_subclass_before_mutation -q` failed before implementation because malformed dictionary-field data executed collection iteration and allowed a model subclass through capability evaluation.
- `pytest tests/test_writeback_orchestration.py::test_evaluate_writeback_capability_rejects_dictionary_field_collection_subclass_without_leak tests/test_writeback_orchestration.py::test_evaluate_writeback_capability_rejects_dictionary_field_item_subclass_without_leak tests/test_writeback_orchestration.py::test_execute_writeback_rejects_dictionary_field_collection_subclass_before_mutation tests/test_writeback_orchestration.py::test_evaluate_writeback_capability_passes_with_state_and_fields tests/test_writeback_orchestration.py::test_execute_writeback_dry_run_does_not_mutate_or_write_audit -q` - 5 passed.
- `pytest tests/test_writeback_orchestration.py::test_evaluate_writeback_capability_rejects_dictionary_field_collection_subclass_without_leak tests/test_writeback_orchestration.py::test_evaluate_writeback_capability_rejects_dictionary_field_item_subclass_without_leak tests/test_writeback_orchestration.py::test_execute_writeback_rejects_dictionary_field_collection_subclass_before_mutation tests/test_project_docs.py::test_sprint_983_documents_writeback_orchestration_dictionary_field_guard -q` - 4 passed.
- `pytest tests/test_writeback_orchestration.py -q` - 35 passed.
- `pytest tests/test_project_docs.py -q` - 1056 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3705 passed, 93.27% coverage.
