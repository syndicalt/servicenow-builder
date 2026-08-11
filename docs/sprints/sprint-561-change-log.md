# Sprint 561 Change Log

## ServiceNow dictionary internal-type length guard

Sprint 561 continued production hardening by bounding ServiceNow dictionary `internal_type` values before configuration writes. `_servicenow_dictionary_internal_type()` already rejected non-string, padded, delimiter-bearing, control-character, and malformed ServiceNow identifier-style type names before `ServiceNowClient.create_story_dictionary_field()` built a `sys_dictionary` POST body, but it did not cap otherwise valid identifier strings.

Dictionary internal-type validation now rejects values longer than 128 characters before OAuth token acquisition, POST body construction, or Table API transport. Oversized internal types fail with the fixed `ServiceNow dictionary internal type is unsafe` diagnostic. The diagnostic does not echo internal type values, body fragments, object representations, or credential-like payloads.

This keeps dictionary field bootstrap and future configuration writes fail-closed when caller input supplies syntactically valid but unbounded ServiceNow type names.

Verification:

- Added 1 failing-first ServiceNow dictionary internal-type length test proving a 129-character identifier reached OAuth token acquisition before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_dictionary_internal_type_before_request -q`: failed before implementation because the oversized internal type reached OAuth token acquisition.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_dictionary_internal_type_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_internal_type_before_request tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_dictionary_internal_type_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_element_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_column_label_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_max_length_before_request tests/test_servicenow.py::test_servicenow_client_creates_story_dictionary_field -q`: 7 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 163 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 635 passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2593 passed, 93.41% total coverage.
