# Sprint 566 Change Log

## ServiceNow metadata response sequence range guard

Sprint 566 continued production hardening by bounding ServiceNow metadata response sequence parsing before state-choice sorting. `_servicenow_metadata_response_int()` already rejected non-integer and malformed `sys_choice.sequence` values before `StoryStateChoice` models were constructed, but it still accepted arbitrary-size Python integers and arbitrary-length ASCII decimal strings.

Metadata response sequence parsing now accepts only non-boolean integers and ASCII decimal strings that fit `0..2147483647`. Missing or blank sequence values still map to `0`. Out-of-range integers and oversized decimal strings fail with the fixed `ServiceNow API metadata response field is unsafe` diagnostic before integer values influence state-choice sorting, lifecycle state discovery, retrieved Update Set handoff, or failure-writeback decisions. The diagnostic does not echo sequence values, state-choice values, object representations, or credential-like payloads.

This keeps ServiceNow metadata discovery fail-closed when a target instance, proxy, or alternate transport returns unbounded numeric ordering metadata.

Verification:

- Added 1 failing-first ServiceNow metadata response sequence range test proving an 11-digit state-choice sequence was accepted before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_state_choice_sequence -q`: failed before implementation because the oversized sequence did not raise `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_state_choice_sequence tests/test_servicenow.py::test_servicenow_client_rejects_non_integer_state_choice_sequence_without_stringifying tests/test_servicenow.py::test_servicenow_client_fetches_story_state_choices_from_sys_choice tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_state_choice_response_flag_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_control_character_metadata_response_text -q`: 5 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 168 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 640 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2603 passed, total coverage 93.40%.
