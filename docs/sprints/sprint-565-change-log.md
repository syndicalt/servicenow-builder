# Sprint 565 Change Log

## ServiceNow metadata response text control-character guard

Sprint 565 continued production hardening by rejecting control-character-bearing ServiceNow metadata response text before metadata model construction. `_servicenow_metadata_response_text()` already rejected non-string and oversized state-choice and dictionary metadata fields returned by ServiceNow before `StoryStateChoice` or `StoryDictionaryField` models were constructed, but it still accepted otherwise valid strings containing ASCII control characters.

Metadata response text validation now rejects ASCII control characters, including newlines and DEL, before state-choice sorting, dictionary-field filtering, metadata model construction, or downstream bootstrap/comparison logic. Ordinary spaces in labels remain valid. Control-character metadata text fails with the fixed `ServiceNow API metadata response field is unsafe` diagnostic. The diagnostic does not echo metadata values, dictionary values, state-choice values, object representations, or credential-like payloads.

This keeps ServiceNow metadata discovery fail-closed when a target instance, proxy, or alternate transport returns line-breaking or terminal-control metadata in state labels, state values, dictionary elements, column labels, or internal types.

Verification:

- Added 1 failing-first ServiceNow metadata response text control-character test proving a newline-bearing state-choice label was accepted before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_control_character_metadata_response_text -q`: failed before implementation because the control-character metadata text did not raise `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_control_character_metadata_response_text tests/test_servicenow.py::test_servicenow_client_rejects_oversized_metadata_response_text tests/test_servicenow.py::test_servicenow_client_rejects_non_string_state_choice_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_non_string_dictionary_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_fetches_story_state_choices_from_sys_choice tests/test_servicenow.py::test_servicenow_client_fetches_active_story_dictionary_fields -q`: 6 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 167 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 639 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2601 passed, total coverage 93.42%.
