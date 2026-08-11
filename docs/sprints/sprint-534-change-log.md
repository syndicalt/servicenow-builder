# Sprint 534 Change Log

## ServiceNow boolean flag serialization guard

Sprint 534 continued production hardening by tightening shared ServiceNow boolean flag serialization. `_bool_query_value()` previously used ordinary truthiness, so non-bool values such as strings, integers, or objects could silently serialize to `true` or `false` before ServiceNow request construction.

ServiceNow flag serialization now accepts only actual Python `bool` values. Non-bool values fail with the fixed `ServiceNow API boolean value is unsafe` diagnostic before OAuth token acquisition, request construction, or API transport. The diagnostic does not echo flag values, object representations, or credential-like payloads.

This protects every ServiceNow request path that uses `_bool_query_value()`, including dictionary `read_only`, CI/CD retrieve `auto_preview` and `cleanup_retrieved`, and CI/CD commit `force_commit`.

Verification:

- Added 1 failing-first ServiceNow boolean flag test proving non-bool CI/CD retrieve flags are rejected before OAuth token acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_cicd_retrieve_flag_before_request -q`: failed before implementation because a string flag was treated as truthy and OAuth token acquisition was attempted.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_cicd_retrieve_flag_before_request tests/test_servicenow.py::test_servicenow_client_retrieves_cicd_update_set_from_update_source tests/test_servicenow.py::test_servicenow_client_previews_commits_and_fetches_cicd_progress tests/test_servicenow.py::test_servicenow_client_creates_story_dictionary_field -q`: 4 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 113 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 608 tests passed after documentation updates.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues across 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2516 tests passed with 93.44% coverage.
