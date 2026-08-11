# Sprint 862 Change Log

## Ready-story project-id truthiness guard

- Added 1 failing-first ready-story project-id truthiness assertion covering hostile `project_sys_id` objects: `test_servicenow_client_rejects_hostile_ready_story_project_id_before_truthiness`.
- `ServiceNowClient.fetch_ready_stories(project_sys_id=...)` now validates provided project ids before truthiness branching.
- `None` still means no project filter; any provided project id must pass the shared record-id guard before the method appends the project clause.

## Verification

- `pytest tests/test_servicenow.py::test_servicenow_client_rejects_hostile_ready_story_project_id_before_truthiness tests/test_project_docs.py::test_sprint_862_documents_ready_story_project_id_truthiness_guard -q` -> 2 passed.
- `pytest tests/test_servicenow.py -q` -> 290 passed.
- `pytest tests/test_project_docs.py -q` -> 935 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` -> 3421 passed, total coverage 93.48%.
