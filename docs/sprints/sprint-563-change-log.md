# Sprint 563 Change Log

## ServiceNow metadata response text length guard

Sprint 563 continued production hardening by bounding ServiceNow metadata response text before metadata model construction. `_servicenow_metadata_response_text()` already rejected non-string state-choice and dictionary metadata fields returned by ServiceNow before `StoryStateChoice` or `StoryDictionaryField` models were constructed, but it did not cap otherwise valid string metadata values.

Metadata response text validation now rejects values longer than 1024 characters before state-choice sorting, dictionary-field filtering, metadata model construction, or downstream bootstrap/comparison logic. Oversized metadata text fails with the fixed `ServiceNow API metadata response field is unsafe` diagnostic. The diagnostic does not echo metadata values, dictionary values, state-choice values, object representations, or credential-like payloads.

This keeps ServiceNow metadata discovery fail-closed when a target instance or alternate transport returns syntactically valid but unbounded labels, values, elements, column labels, or internal types.

Verification:

- Added 1 failing-first ServiceNow metadata response text length test proving a 1025-character state-choice label was accepted before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_metadata_response_text -q`: failed before implementation because the oversized metadata text did not raise `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_metadata_response_text tests/test_servicenow.py::test_servicenow_client_rejects_non_string_state_choice_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_fetches_story_state_choices_from_sys_choice tests/test_servicenow.py::test_servicenow_client_fetches_active_story_dictionary_fields tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_state_choice_response_flag_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_non_integer_state_choice_sequence_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_non_string_dictionary_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_dictionary_response_flag_without_stringifying -q`: 8 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 165 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 637 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2597 passed, total coverage 93.42%.
