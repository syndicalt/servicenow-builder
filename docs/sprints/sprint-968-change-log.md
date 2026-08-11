# Sprint 968 Change Log - Retrieved Update Set handoff story sys_id guard

## Summary

Hardened retrieved Update Set handoff story writeback identifiers so corrupted in-process `UpdateSetHandoffRequest.story_sys_id` values cannot reach the ServiceNow client or trigger import side effects.

`create_update_set_handoff()` now validates `story_sys_id` through `_handoff_story_sys_id()` before candidate routing or retrieved Update Set import. The helper accepts only exact Python strings. Non-string values and string subclasses fail closed with `retrieved Update Set handoff story sys_id contains non-JSON value`.

## Security impact

- Malformed story sys_ids fail before customer-update generation, XML serialization, ServiceNow import, story field updates, or work-note formatting.
- The handoff no longer passes corrupted story identifiers into client adapters that may stringify or serialize them.
- Normal validated runtime requests continue to use exact string sys_ids.

## Tests

- Added 1 failing-first retrieved Update Set handoff story sys_id assertion: `test_create_update_set_handoff_rejects_story_sys_id_object_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_968_documents_handoff_story_sys_id_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_story_sys_id_object_without_leak -q` failed before implementation because malformed story sys_id values were accepted.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_story_sys_id_object_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 2 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_story_sys_id_object_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story tests/test_project_docs.py::test_sprint_968_documents_handoff_story_sys_id_guard -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py -q` - 46 passed.
- `pytest tests/test_project_docs.py -q` - 1041 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed with no issues in 203 source files.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3661 passed, total coverage 93.23%.
