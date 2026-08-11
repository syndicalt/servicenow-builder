# Sprint 864 Change Log

## ServiceNow CI/CD source-id truthiness guard

- Added 2 failing-first ServiceNow CI/CD source-id truthiness assertions covering hostile `update_source_id` and `update_source_instance_id` objects: `test_servicenow_client_rejects_cicd_retrieve_source_ids_before_truthiness`.
- `ServiceNowClient.retrieve_cicd_update_set()` now validates optional source ids before truthiness branching.
- `None` still omits optional `update_source_id` and `update_source_instance_id` parameters; any provided source id must pass the shared record-id guard before parameter inclusion.

## Verification

- `pytest tests/test_servicenow.py::test_servicenow_client_rejects_cicd_retrieve_source_ids_before_truthiness tests/test_project_docs.py::test_sprint_864_documents_cicd_source_id_truthiness_guard -q` -> 3 passed.
- `pytest tests/test_servicenow.py -q` -> 293 passed.
- `pytest tests/test_project_docs.py -q` -> 937 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` -> 3426 passed, total coverage 93.50%.
