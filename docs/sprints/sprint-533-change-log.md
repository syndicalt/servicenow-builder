# Sprint 533 Change Log

## ServiceNow CI/CD retrieve id validation

Sprint 533 continued production hardening by tightening `ServiceNowClient.retrieve_cicd_update_set()`. CI/CD preview, commit, and progress path ids already used the ServiceNow record-id rule, but retrieve query parameters still accepted `update_set_id`, `update_source_id`, and `update_source_instance_id` raw until OAuth acquisition and request construction.

CI/CD retrieve now validates those id parameters with the same record-id safety rule before adding them to query parameters. Unsafe ids fail with the fixed `ServiceNow API record id is unsafe` diagnostic before OAuth token acquisition, request construction, or CI/CD API transport. The diagnostic does not echo CI/CD ids, URL fragments, query fragments, or credential-like payloads.

This keeps all CI/CD Update Set identity parameters consistent across retrieve, preview, commit, and progress operations.

Verification:

- Added 1 failing-first ServiceNow CI/CD retrieve id test proving unsafe retrieve ids are rejected before OAuth token acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_cicd_retrieve_update_set_id_before_request -q`: failed before implementation because OAuth token acquisition was attempted before retrieve id validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_cicd_retrieve_update_set_id_before_request tests/test_servicenow.py::test_servicenow_client_retrieves_cicd_update_set_from_update_source -q`: 2 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 112 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 607 documentation tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2514 tests passed with 93.44% coverage.
