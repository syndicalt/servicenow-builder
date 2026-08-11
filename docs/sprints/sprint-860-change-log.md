# Sprint 860 Change Log

## Completion notifier story-sys-id guard

- Added 1 failing-first completion story-sys-id assertion covering malformed completion lifecycle `story_sys_id` values: `test_servicenow_complete_notifier_rejects_unsafe_story_sys_id`.
- `_servicenow_complete_notifier()` now validates completion record ids before closeout field update.
- Malformed completion ids fail with the fixed `completed story_sys_id is unsafe` diagnostic before `update_story_fields()` is called.

## Verification

- `pytest tests/test_runtime.py::test_servicenow_complete_notifier_rejects_unsafe_story_sys_id tests/test_project_docs.py::test_sprint_860_documents_completion_story_sys_id_guard -q` -> 2 passed.
- `pytest tests/test_runtime.py -q -k "servicenow_complete_notifier"` -> 4 passed, 416 deselected.
- `pytest tests/test_project_docs.py -q` -> 933 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` -> 3417 passed, total coverage 93.48%.
