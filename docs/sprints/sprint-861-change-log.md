# Sprint 861 Change Log

## ServiceNow story query guard

- Added 1 failing-first ServiceNow story-query assertion covering hostile raw `sysparm_query` inputs: `test_servicenow_client_rejects_unsafe_story_query_before_request`.
- `ServiceNowClient.fetch_stories()` now validates raw story query inputs before request construction.
- Unsafe story queries fail with the fixed `ServiceNow API story query is unsafe` diagnostic before truthiness checks, OAuth token acquisition, GET construction, or Table API transport.

## Verification

- `pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_query_before_request tests/test_project_docs.py::test_sprint_861_documents_servicenow_story_query_guard -q` -> 2 passed.
- `pytest tests/test_servicenow.py -q` -> 289 passed.
- `pytest tests/test_project_docs.py -q` -> 934 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` -> 3419 passed, total coverage 93.48%.
