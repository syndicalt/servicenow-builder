# Sprint 547 Change Log

## ServiceNow attachment metadata type guards

Sprint 547 continued production hardening by tightening ServiceNow story attachment upload metadata validation. Sprint 528 moved `file_name` and `content_type` validation before local file reads, but `_servicenow_attachment_file_name()` and `_servicenow_attachment_content_type()` still called string methods before proving metadata values were strings. Hostile non-string metadata objects could therefore raise Python `AttributeError` diagnostics containing object representations before the fixed ServiceNow validation diagnostics were used.

Attachment metadata validation now rejects non-string file names and content types before string-method calls, length checks, separator checks, whitespace/control checks, or MIME token regex matching. Non-string or malformed metadata fails with the fixed diagnostics `ServiceNow attachment file name is unsafe` or `ServiceNow attachment content type is unsafe` before local artifact reads, OAuth token acquisition, Attachment API request construction, or Table API transport. Diagnostics do not echo object type names, object string output, submitted metadata values, URL fragments, header-injection text, or credential-like payloads.

This protects `ServiceNowClient.attach_story_file()` before it reads attachment bytes or constructs the Attachment API request.

Verification:

- Added 2 failing-first ServiceNow attachment metadata type tests proving hostile non-string file name and content type values are rejected before local file reads, OAuth token acquisition, or request construction and without calling `str()` or `repr()` for diagnostics.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_attachment_file_name_before_read tests/test_servicenow.py::test_servicenow_client_rejects_non_string_attachment_content_type_before_read -q`: failed before implementation because both validators raised `AttributeError` with hostile object representations.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_attachment_file_name_before_read tests/test_servicenow.py::test_servicenow_client_rejects_non_string_attachment_content_type_before_read tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_file_name_before_read tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_attachment_content_type_before_read tests/test_servicenow.py::test_servicenow_client_uploads_story_attachment_with_binary_body -q`: 5 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 128 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 621 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2544 tests passed with 93.46% coverage.
