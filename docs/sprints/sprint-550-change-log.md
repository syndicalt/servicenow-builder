# Sprint 550 Change Log

## ServiceNow metadata response boolean type guard

Sprint 550 continued production hardening by tightening ServiceNow metadata response boolean parsing. `_state_choice_from_record()` and `_dictionary_field_from_record()` previously used the broad `_truthy()` helper for `inactive`, `active`, and `read_only` response flags. That helper called `str()` on arbitrary non-bool values and treated unknown strings as false, so a hostile or corrupted alternate transport response could silently misclassify metadata availability before a fixed ServiceNow response diagnostic was used.

Metadata response boolean parsing now accepts only actual booleans and explicit string boolean values from ServiceNow. Non-string objects and malformed boolean strings fail with the fixed `ServiceNow API metadata response field is unsafe` diagnostic before `StoryStateChoice` or `StoryDictionaryField` models are constructed. The diagnostic does not echo object type names, object string output, metadata flag values, dictionary values, state-choice values, or credential-like payloads.

This protects active state-choice discovery, active dictionary field discovery, and read-only metadata interpretation before those values influence bootstrap, lifecycle, or failure-writeback decisions.

Verification:

- Added 2 failing-first ServiceNow metadata response boolean tests proving hostile non-bool state-choice and dictionary response flags are rejected without stringifying object output or silently treating the values as false.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_state_choice_response_flag_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_dictionary_response_flag_without_stringifying -q`: failed before implementation because both parsers accepted hostile objects by calling `str()`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_state_choice_response_flag_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_dictionary_response_flag_without_stringifying tests/test_servicenow.py::test_servicenow_client_fetches_story_state_choices_from_sys_choice tests/test_servicenow.py::test_servicenow_client_fetches_active_story_dictionary_fields -q`: 4 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 133 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 624 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2552 tests passed with 93.45% coverage.
