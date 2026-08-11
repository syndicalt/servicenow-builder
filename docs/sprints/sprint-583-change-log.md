# Sprint 583 Change Log

## ServiceNow story response text string-subclass guard

Sprint 583 continued production hardening by preventing ServiceNow story response text parsing from dispatching string methods on hostile string subclasses. `_servicenow_story_response_text()` already rejected non-string story text values before `Story` model construction, but it still accepted `str` subclasses and returned them to downstream helpers such as `_optional_servicenow_story_response_text()`, where optional acceptance criteria called `strip()` before returning the fixed `ServiceNow API story response field is unsafe` diagnostic.

Story response text parsing now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow API story response field is unsafe` diagnostic before optional acceptance-criteria trimming, additional-context length checks, `Story` model construction, automation routing, operational views, artifact persistence, or failure-writeback decisions. This preserves normal ServiceNow JSON string handling while preventing alternate transports, tests, or malformed responses from surfacing custom exception text, object representations, or credential-like payloads through story text string methods.

This keeps `ServiceNowClient.fetch_stories()` fail-closed before constructing `Story` models from unsafe required story fields, optional acceptance criteria, or AI additional-context fields.

Verification:

- Added 1 failing-first ServiceNow story response text string-subclass test proving a hostile `str` subclass raised `RuntimeError` from overridden `strip()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_response_text_str_subclass -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from overridden `strip()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_response_text_str_subclass tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_additional_context tests/test_servicenow.py::test_servicenow_client_maps_missing_optional_record_values_to_safe_defaults tests/test_servicenow.py::test_servicenow_client_requests_and_maps_writeback_idempotency_fields -q`: 5 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_583_documents_servicenow_story_response_text_str_subclass_guard -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 186 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 657 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2638 passed, 93.39% coverage.
