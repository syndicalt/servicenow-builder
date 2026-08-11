# Sprint 551 Change Log

## ServiceNow metadata response sequence type guard

Sprint 551 continued production hardening by tightening ServiceNow metadata response integer parsing. `_state_choice_from_record()` previously converted the `sys_choice.sequence` response field with `int(record.get("sequence") or 0)`. A hostile or corrupted alternate transport response could therefore raise Python integer-conversion diagnostics containing object type names before the fixed ServiceNow response diagnostic was used.

Metadata response sequence parsing now accepts only actual non-boolean integers and simple ASCII decimal strings from ServiceNow. Missing or blank sequence values still map to `0`; non-string objects, booleans, signed values, whitespace-padded values, non-ASCII digits, and malformed strings fail with the fixed `ServiceNow API metadata response field is unsafe` diagnostic before `StoryStateChoice` models are constructed. The diagnostic does not echo object type names, object string output, sequence values, state-choice values, or credential-like payloads.

This protects active state-choice sorting before sequence values influence lifecycle state discovery, retrieved Update Set handoff, or failure-writeback decisions.

Verification:

- Added 1 failing-first ServiceNow metadata response sequence test proving a hostile non-integer state-choice sequence is rejected without stringifying object output or surfacing Python conversion diagnostics.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_integer_state_choice_sequence_without_stringifying -q`: failed before implementation because `_state_choice_from_record()` called `int()` on the hostile object.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_integer_state_choice_sequence_without_stringifying tests/test_servicenow.py::test_servicenow_client_fetches_story_state_choices_from_sys_choice tests/test_servicenow.py::test_servicenow_client_rejects_non_bool_state_choice_response_flag_without_stringifying -q`: 3 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 134 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 625 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2554 tests passed; required 90% coverage reached with 93.43% total coverage.
