# Sprint 546 Change Log

## ServiceNow dictionary internal type type guard

Sprint 546 continued production hardening by tightening ServiceNow dictionary field creation. Sprint 536 added an identifier-shape guard for `internal_type`, but `_servicenow_dictionary_internal_type()` still called string methods before proving the value was a string. Hostile non-string internal type objects could therefore raise Python `AttributeError` diagnostics containing object representations before the fixed ServiceNow validation diagnostic was used.

Dictionary internal type validation now rejects non-string values before padding checks or identifier regex matching. Non-string, padded, delimiter-bearing, control-character, or malformed internal types fail with the fixed `ServiceNow dictionary internal type is unsafe` diagnostic before OAuth token acquisition, POST construction, or Table API transport. The diagnostic does not echo object type names, object string output, internal type values, body fragments, or credential-like payloads.

This protects `ServiceNowClient.create_story_dictionary_field()` before it constructs the `sys_dictionary` request body.

Verification:

- Added 1 failing-first ServiceNow dictionary internal type test proving a hostile non-string internal type is rejected before OAuth token acquisition or request construction and without calling `str()` or `repr()` for diagnostics.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_dictionary_internal_type_before_request -q`: failed before implementation because `_servicenow_dictionary_internal_type()` raised `AttributeError` with a hostile object representation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_dictionary_internal_type_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_internal_type_before_request tests/test_servicenow.py::test_servicenow_client_creates_story_dictionary_field -q`: 3 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 126 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 620 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2541 tests passed with 93.46% coverage.
