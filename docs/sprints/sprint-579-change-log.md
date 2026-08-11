# Sprint 579 Change Log

## ServiceNow attachment file-name string-subclass guard

Sprint 579 continued production hardening by preventing ServiceNow attachment file-name validation from dispatching string methods on hostile string subclasses. `_servicenow_attachment_file_name()` already rejected non-string values, blank names, trim-padded names, special path names, oversized names, path separators, whitespace, and control characters before local attachment reads or Attachment API request construction, but it still accepted `str` subclasses and called `strip()` before returning the fixed `ServiceNow attachment file name is unsafe` diagnostic.

Attachment file-name validation now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow attachment file name is unsafe` diagnostic before trim checks, special-name checks, length checks, path-separator checks, whitespace/control-character scans, local artifact reads, OAuth token acquisition, Attachment API request construction, or transport calls. This preserves normal attachment uploads while preventing internal caller wiring, tests, or future adapters from surfacing custom exception text, object representations, or credential-like payloads through file-name string methods.

This keeps `ServiceNowClient.attach_story_file()` fail-closed before reading local artifacts or constructing Attachment API writes from unsafe `file_name` objects.

Verification:

- Added 1 failing-first ServiceNow attachment file-name string-subclass test proving a hostile `str` subclass raised `RuntimeError` from overridden `strip()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_attachment_file_name_str_subclass_before_read -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from overridden `strip()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_attachment_file_name_str_subclass_before_read tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_file_name_before_read tests/test_servicenow.py::test_servicenow_client_rejects_non_string_attachment_file_name_before_read tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_with_binary_body -q`: 4 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_579_documents_servicenow_attachment_file_name_str_subclass_guard -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 181 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 653 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2629 passed, 93.39% coverage.
