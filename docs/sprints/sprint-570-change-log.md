# Sprint 570 Change Log

## ServiceNow metadata sequence integer-subclass guard

Sprint 570 continued production hardening by preventing ServiceNow metadata sequence parsing from dispatching comparisons on hostile integer subclasses. `_servicenow_metadata_response_int()` already rejected malformed strings, string subclasses, booleans, and out-of-range `sys_choice.sequence` values before `StoryStateChoice` models were constructed, but it still accepted `int` subclasses and compared them against the allowed sequence range.

Metadata response sequence parsing now accepts exact `int` values and exact `str` decimal values only. Integer subclasses fail with the fixed `ServiceNow API metadata response field is unsafe` diagnostic before range comparisons, integer conversion, state-choice sorting, lifecycle state discovery, retrieved Update Set handoff, or failure-writeback decisions. This preserves normal JSON integer handling while preventing alternate transports from surfacing custom exception text, object representations, or credential-like payloads through sequence range checks.

This keeps ServiceNow metadata discovery fail-closed when a test transport, mock transport, or future response adapter returns a hostile integer subclass for `sys_choice.sequence`.

Verification:

- Added 1 failing-first ServiceNow metadata response sequence integer-subclass test proving a hostile `int` subclass could execute comparison methods and raise credential-bearing exception text before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_state_choice_sequence_int_subclass_without_comparing -q`: failed before implementation because the hostile integer subclass raised `RuntimeError` during range comparison instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_state_choice_sequence_int_subclass_without_comparing tests/test_servicenow.py::test_servicenow_client_rejects_state_choice_sequence_str_subclass_without_methods tests/test_servicenow.py::test_servicenow_client_rejects_non_integer_state_choice_sequence_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_oversized_state_choice_sequence tests/test_servicenow.py::test_servicenow_client_fetches_story_state_choices_from_sys_choice -q`: 5 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 172 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 644 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2611 passed, total coverage 93.40%.
