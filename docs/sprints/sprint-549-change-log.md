# Sprint 549 Change Log

## ServiceNow metadata response text type guard

Sprint 549 continued production hardening by tightening ServiceNow metadata response ingestion. `_state_choice_from_record()` and `_dictionary_field_from_record()` previously converted state-choice labels/values and dictionary field text with `str()`. A hostile or corrupted alternate transport response could therefore place object string output into `StoryStateChoice` or `StoryDictionaryField` values before a fixed ServiceNow response diagnostic was used.

Metadata response parsing now accepts only string values for story state-choice label/value fields and story dictionary `element`, `column_label`, and `internal_type` fields. Non-string metadata text fails with the fixed `ServiceNow API metadata response field is unsafe` diagnostic before typed metadata models are constructed. The diagnostic does not echo object type names, object string output, metadata values, dictionary values, state-choice values, or credential-like payloads.

This protects `ServiceNowClient.fetch_story_state_choices()` and `ServiceNowClient.fetch_story_dictionary_fields()` before ServiceNow metadata leaves the client boundary and influences bootstrap, workflow state discovery, or dictionary validation decisions.

Verification:

- Added 2 failing-first ServiceNow metadata response text tests proving hostile non-string state-choice and dictionary response fields are rejected without stringifying object output into typed metadata models.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_state_choice_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_non_string_dictionary_response_text_without_stringifying -q`: failed before implementation because both parsers accepted hostile objects by calling `str()`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_state_choice_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_non_string_dictionary_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_fetches_story_state_choices_from_sys_choice tests/test_servicenow.py::test_servicenow_client_fetches_active_story_dictionary_fields -q`: 4 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 131 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 623 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2549 tests passed with 93.44% coverage.
