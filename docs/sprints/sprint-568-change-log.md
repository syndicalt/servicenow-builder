# Sprint 568 Change Log

## ServiceNow metadata text string-subclass guard

Sprint 568 continued production hardening by preventing ServiceNow metadata text parsing from accepting string subclasses before metadata model construction. `_servicenow_metadata_response_text()` already rejected non-string, oversized, and control-character-bearing state-choice and dictionary metadata fields before `StoryStateChoice` or `StoryDictionaryField` models were constructed, but it still accepted `str` subclasses and returned them into typed metadata models.

Metadata response text parsing now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow API metadata response field is unsafe` diagnostic before state-choice sorting, dictionary-field filtering, metadata model construction, or downstream bootstrap/comparison logic. This preserves normal JSON string handling while preventing alternate transports from carrying subclass behavior or subclass identity into application metadata.

This keeps ServiceNow metadata discovery fail-closed when a test transport, mock transport, or future response adapter returns a hostile string subclass for state labels, state values, dictionary elements, column labels, or internal types.

Verification:

- Added 1 failing-first ServiceNow metadata response text string-subclass test proving a `str` subclass state-choice label was accepted before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_metadata_text_str_subclass -q`: failed before implementation because the string subclass did not raise `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_metadata_text_str_subclass tests/test_servicenow.py::test_servicenow_client_rejects_non_string_state_choice_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_oversized_metadata_response_text tests/test_servicenow.py::test_servicenow_client_rejects_control_character_metadata_response_text tests/test_servicenow.py::test_servicenow_client_rejects_non_string_dictionary_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_fetches_story_state_choices_from_sys_choice tests/test_servicenow.py::test_servicenow_client_fetches_active_story_dictionary_fields -q`: 7 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 170 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 642 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2607 passed, total coverage 93.40%.
