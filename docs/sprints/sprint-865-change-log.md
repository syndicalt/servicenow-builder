# Sprint 865 Change Log

## ServiceNow CI/CD probe action guard

- Added 1 failing-first ServiceNow CI/CD probe-action assertion covering hostile `action` objects: `test_servicenow_cicd_probe_rejects_unsafe_action_before_membership`.
- `ServiceNowClient.probe_cicd_update_set_endpoint()` now validates probe actions before membership checks.
- Unsafe probe actions fail with the fixed `ServiceNow CI/CD probe action is unsafe` diagnostic before OAuth token acquisition, URL construction, request construction, or API transport.

## Verification

- `pytest tests/test_servicenow.py::test_servicenow_cicd_probe_rejects_unsafe_action_before_membership tests/test_project_docs.py::test_sprint_865_documents_cicd_probe_action_guard -q` -> 2 passed.
- `pytest tests/test_servicenow.py -q` -> 294 passed.
- `pytest tests/test_project_docs.py -q` -> 938 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` -> 3428 passed, total coverage 93.51%.
