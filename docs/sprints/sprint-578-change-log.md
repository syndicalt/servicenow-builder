# Sprint 578 Change Log

## ServiceNow dictionary column-label string-subclass guard

Sprint 578 continued production hardening by preventing ServiceNow dictionary column-label validation from dispatching string methods on hostile string subclasses. `_servicenow_dictionary_column_label()` already rejected non-string, blank, padded, control-character, oversized, and malformed column labels before OAuth token acquisition or request construction, but it still accepted `str` subclasses and called `strip()` before returning the fixed `ServiceNow dictionary column label is unsafe` diagnostic.

Dictionary column-label validation now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow dictionary column label is unsafe` diagnostic before blank-label checks, `strip()`, length checks, control-character scans, dictionary request body construction, OAuth token acquisition, or transport calls. This preserves normal dictionary field creation while preventing internal caller wiring, tests, or future adapters from surfacing custom exception text, object representations, or credential-like payloads through column-label string methods.

This keeps `ServiceNowClient.create_story_dictionary_field()` fail-closed before constructing `sys_dictionary` writes from unsafe `column_label` objects.

Verification:

- Added 1 failing-first ServiceNow dictionary column-label string-subclass test proving a hostile `str` subclass raised `RuntimeError` from overridden `strip()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_dictionary_column_label_str_subclass -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from overridden `strip()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_dictionary_column_label_str_subclass tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_column_label_before_request tests/test_servicenow.py::test_servicenow_client_creates_story_dictionary_field -q`: 3 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_578_documents_servicenow_dictionary_column_label_str_subclass_guard -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 180 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 652 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2627 passed, 93.39% coverage.
