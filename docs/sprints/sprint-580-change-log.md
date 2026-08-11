# Sprint 580 Change Log

## ServiceNow attachment content-type string-subclass guard

Sprint 580 continued production hardening by preventing ServiceNow attachment content-type validation from dispatching string methods on hostile string subclasses. `_servicenow_attachment_content_type()` already rejected non-string values, trim-padded values, oversized values, malformed MIME tokens, whitespace, and control characters before local attachment reads or Attachment API request construction, but it still accepted `str` subclasses and called `strip()` before returning the fixed `ServiceNow attachment content type is unsafe` diagnostic.

Attachment content-type validation now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow attachment content type is unsafe` diagnostic before trim checks, length checks, MIME token pattern matching, local artifact reads, OAuth token acquisition, Attachment API request construction, header construction, or transport calls. This preserves normal attachment uploads while preventing internal caller wiring, tests, or future adapters from surfacing custom exception text, object representations, or credential-like payloads through content-type string methods.

This keeps `ServiceNowClient.attach_story_file()` fail-closed before reading local artifacts or constructing Attachment API writes from unsafe `content_type` objects.

Verification:

- Added 1 failing-first ServiceNow attachment content-type string-subclass test proving a hostile `str` subclass raised `RuntimeError` from overridden `strip()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_attachment_content_type_str_subclass_before_read -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from overridden `strip()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_attachment_content_type_str_subclass_before_read tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_content_type_before_read tests/test_servicenow.py::test_servicenow_client_rejects_non_string_attachment_content_type_before_read tests/test_servicenow.py::test_servicenow_client_rejects_oversized_attachment_content_type_before_read tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_with_binary_body -q`: 5 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_580_documents_servicenow_attachment_content_type_str_subclass_guard -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 182 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 654 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2631 passed, 93.39% coverage.
