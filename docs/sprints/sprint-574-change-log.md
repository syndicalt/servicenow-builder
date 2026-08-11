# Sprint 574 Change Log

## ServiceNow record-id string-subclass guard

Sprint 574 continued production hardening by preventing ServiceNow record-id validation from dispatching string methods on hostile string subclasses. `_servicenow_record_id()` already rejected non-string, padded, path-delimiter, oversized, and malformed record ids before OAuth token acquisition or request construction, but it still accepted `str` subclasses and called `strip()` before returning the fixed `ServiceNow API record id is unsafe` diagnostic.

Record-id validation now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow API record id is unsafe` diagnostic before `strip()`, length checks, regex matching, OAuth token acquisition, Table API URL construction, CI/CD path construction, attachment reads, or transport calls. This preserves normal record-id handling while preventing internal caller wiring, tests, or future adapters from surfacing custom exception text, object representations, or credential-like payloads through record-id string methods.

This keeps `ServiceNowClient.update_story_fields()`, lookup-derived update paths, CI/CD Update Set paths, ready-story project filters, and attachment target ids fail-closed before constructing ServiceNow URL paths or encoded-query fragments from unsafe record-id objects.

Verification:

- Added 1 failing-first ServiceNow record-id string-subclass test proving a hostile `str` subclass raised `RuntimeError` from overridden `strip()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_record_id_str_subclass_without_methods -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from overridden `strip()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_record_id_str_subclass_without_methods tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_record_id_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_record_id_before_request tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_record_id_before_request tests/test_servicenow.py::test_servicenow_client_updates_story_fields_with_patch_without_secret_leakage -q`: 5 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 176 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 648 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2619 passed, total coverage 93.38%.
