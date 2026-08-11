# Sprint 859 Change Log

## Failure notifier lookup-result sys-id guard

- Added 1 failing-first failure notifier lookup-result assertion covering malformed story `sys_id` values returned from ServiceNow lookup: `test_servicenow_failure_notifier_rejects_unsafe_found_story_sys_id`.
- `_servicenow_failure_notifier()` now validates found story identifiers before failed-story field update.
- Malformed lookup results fail with the fixed `story lookup result is unsafe` diagnostic before `update_story_fields()` is called.

## Verification

- `pytest tests/test_runtime.py::test_servicenow_failure_notifier_rejects_unsafe_found_story_sys_id tests/test_project_docs.py::test_sprint_859_documents_failure_notifier_lookup_result_guard -q` -> 2 passed.
- `pytest tests/test_runtime.py -q -k "servicenow_failure_notifier"` -> 9 passed, 410 deselected.
- `pytest tests/test_project_docs.py -q` -> 932 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` -> 3415 passed, total coverage 93.48%.
