# Sprint 567 Change Log

## ServiceNow metadata boolean string-subclass guard

Sprint 567 continued production hardening by preventing ServiceNow metadata boolean parsing from dispatching methods on hostile string subclasses. `_servicenow_metadata_response_bool()` already rejected non-boolean objects, malformed strings, and padded strings before `StoryStateChoice` or `StoryDictionaryField` models were constructed, but it still accepted `str` subclasses and called `.lower()` on them.

Metadata response boolean parsing now accepts actual booleans and exact `str` values only. String subclasses fail with the fixed `ServiceNow API metadata response field is unsafe` diagnostic before `.lower()` or any subclass-controlled method can run. This preserves normal JSON string handling while preventing alternate transports from surfacing custom exception text, object representations, or credential-like payloads through boolean normalization.

This keeps ServiceNow metadata discovery fail-closed when a test transport, mock transport, or future response adapter returns a hostile string subclass for `inactive`, `active`, or `read_only`.

Verification:

- Added 1 failing-first ServiceNow metadata response boolean string-subclass test proving a hostile `str` subclass could execute `.lower()` and raise credential-bearing exception text before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_metadata_boolean_str_subclass_without_lowering -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from `.lower()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_metadata_boolean_str_subclass_without_lowering tests/test_servicenow.py::test_servicenow_client_rejects_padded_metadata_boolean_response_flag tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_state_choice_response_flag_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_dictionary_response_flag_without_stringifying tests/test_servicenow.py::test_servicenow_client_fetches_story_state_choices_from_sys_choice tests/test_servicenow.py::test_servicenow_client_fetches_active_story_dictionary_fields -q`: 6 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 169 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 641 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2605 passed, total coverage 93.40%.
