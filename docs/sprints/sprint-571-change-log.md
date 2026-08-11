# Sprint 571 Change Log

## ServiceNow story response priority integer-subclass guard

Sprint 571 continued production hardening by preventing ServiceNow story response priority parsing from accepting hostile integer subclasses. `_servicenow_story_response_int()` already rejected non-integer objects, booleans, signed strings, whitespace-padded strings, non-ASCII digits, and malformed decimal strings before `Story` models were constructed, but it still accepted `int` subclasses as numeric priority values.

Story response priority parsing now accepts exact `int` values and exact `str` decimal values only. Integer subclasses fail with the fixed `ServiceNow API story response field is unsafe` diagnostic before `Story` validation, automation routing, operational views, work-note generation, artifact persistence, or failure-writeback decisions. This preserves normal JSON integer handling while preventing alternate transports from passing custom integer subclasses through the story ingestion boundary.

This keeps ServiceNow story ingestion fail-closed when a test transport, mock transport, or future response adapter returns a hostile integer subclass for the story `priority` field.

Verification:

- Added 1 failing-first ServiceNow story response priority integer-subclass test proving the client accepted the hostile integer subclass before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_priority_int_subclass_before_validation -q`: failed before implementation because the client accepted the hostile integer subclass instead of raising `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_priority_int_subclass_before_validation tests/test_servicenow.py::test_servicenow_client_rejects_non_integer_story_priority_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_malformed_story_priority_values tests/test_servicenow.py::test_servicenow_client_maps_missing_optional_record_values_to_safe_defaults tests/test_servicenow.py::test_servicenow_client_maps_records_to_validated_stories -q`: 11 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 173 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 645 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2613 passed, total coverage 93.39%.
