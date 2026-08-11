# Sprint 569 Change Log

## ServiceNow metadata sequence string-subclass guard

Sprint 569 continued production hardening by preventing ServiceNow metadata sequence parsing from dispatching methods on hostile string subclasses. `_servicenow_metadata_response_int()` already rejected non-integer, malformed, and out-of-range `sys_choice.sequence` values before `StoryStateChoice` models were constructed, but it still accepted `str` subclasses and called `.isascii()` and `.isdecimal()` on them.

Metadata response sequence parsing now accepts actual non-boolean integers and exact `str` decimal values only. String subclasses fail with the fixed `ServiceNow API metadata response field is unsafe` diagnostic before `.isascii()`, `.isdecimal()`, integer conversion, state-choice sorting, lifecycle state discovery, retrieved Update Set handoff, or failure-writeback decisions. This preserves normal JSON string handling while preventing alternate transports from surfacing custom exception text, object representations, or credential-like payloads through sequence normalization.

This keeps ServiceNow metadata discovery fail-closed when a test transport, mock transport, or future response adapter returns a hostile string subclass for `sys_choice.sequence`.

Verification:

- Added 1 failing-first ServiceNow metadata response sequence string-subclass test proving a hostile `str` subclass could execute `.isascii()` and raise credential-bearing exception text before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_state_choice_sequence_str_subclass_without_methods -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from `.isascii()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_state_choice_sequence_str_subclass_without_methods tests/test_servicenow.py::test_servicenow_client_rejects_non_integer_state_choice_sequence_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_oversized_state_choice_sequence tests/test_servicenow.py::test_servicenow_client_fetches_story_state_choices_from_sys_choice tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_state_choice_response_flag_without_stringifying -q`: 5 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 171 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 643 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2609 passed, total coverage 93.40%.
