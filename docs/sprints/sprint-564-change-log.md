# Sprint 564 Change Log

## ServiceNow metadata response boolean padding guard

Sprint 564 continued production hardening by making ServiceNow metadata response boolean parsing strict on padding. `_servicenow_metadata_response_bool()` already rejected non-boolean objects and malformed boolean strings before `StoryStateChoice` or `StoryDictionaryField` models were constructed, but it still stripped whitespace before interpretation.

Metadata response boolean parsing now accepts actual booleans and exact case-insensitive string boolean values only. Padded values such as ` true ` fail with the fixed `ServiceNow API metadata response field is unsafe` diagnostic before state-choice filtering, dictionary-field filtering, metadata model construction, or downstream bootstrap/comparison logic. The diagnostic does not echo metadata flag values, dictionary values, state-choice values, object representations, or credential-like payloads.

This keeps ServiceNow metadata discovery fail-closed when a target instance, proxy, or alternate transport returns ambiguous boolean flags for `inactive`, `active`, or `read_only`.

Verification:

- Added 1 failing-first ServiceNow metadata response boolean padding test proving a padded dictionary `active` flag was accepted before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_padded_metadata_boolean_response_flag -q`: failed before implementation because the padded boolean did not raise `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_padded_metadata_boolean_response_flag tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_state_choice_response_flag_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_dictionary_response_flag_without_stringifying tests/test_servicenow.py::test_servicenow_client_fetches_story_state_choices_from_sys_choice tests/test_servicenow.py::test_servicenow_client_fetches_active_story_dictionary_fields -q`: 5 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 166 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 638 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2599 passed, total coverage 93.42%.
