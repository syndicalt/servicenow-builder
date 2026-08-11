# Sprint 981 Change Log - Retrieved Update Set handoff state choice guard

## Summary

Hardened retrieved Update Set handoff Ready-for-Testing state lookup so malformed ServiceNow state-choice collections cannot execute iteration or model hooks before story writeback planning.

`_ready_for_testing_state()` now routes `fetch_story_state_choices()` through `_handoff_state_choices()`. The helper accepts only exact Python lists containing exact `StoryStateChoice` records and fails closed with `retrieved Update Set handoff state choices contain non-JSON value`.

## Security impact

- Malformed state-choice collections fail before iteration hooks, `model_dump()` calls, state mapping construction, story field updates, work-note formatting, or returned handoff metadata.
- Malformed state-choice items fail before model-subclass hooks can run.
- Diagnostics do not include collection type names, item type names, hook output, or credential-like fragments.
- This guard runs after retrieved Update Set import, so a failure leaves the review artifact imported but prevents story writeback.

## Tests

- Added 1 failing-first state-choice collection assertion: `test_create_update_set_handoff_rejects_state_choice_collection_subclass_without_leak`.
- Added 1 state-choice item assertion: `test_create_update_set_handoff_rejects_state_choice_item_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_981_documents_handoff_state_choice_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_state_choice_collection_subclass_without_leak -q` failed before implementation because a malformed state-choice list subclass executed `__iter__`.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_state_choice_collection_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 2 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_state_choice_collection_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_state_choice_item_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_state_choice_collection_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_state_choice_item_subclass_without_leak tests/test_project_docs.py::test_sprint_981_documents_handoff_state_choice_guard -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py -q` - 57 passed.
- `pytest tests/test_project_docs.py -q` - 1054 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3697 passed, 93.26% coverage.
