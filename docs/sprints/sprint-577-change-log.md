# Sprint 577 Change Log

## ServiceNow dictionary internal-type string-subclass guard

Sprint 577 continued production hardening by preventing ServiceNow dictionary internal-type validation from dispatching string methods on hostile string subclasses. `_servicenow_dictionary_internal_type()` already rejected non-string, padded, delimiter-bearing, oversized, and malformed internal type values before OAuth token acquisition or request construction, but it still accepted `str` subclasses and called `strip()` before returning the fixed `ServiceNow dictionary internal type is unsafe` diagnostic.

Dictionary internal-type validation now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow dictionary internal type is unsafe` diagnostic before `strip()`, length checks, regex matching, dictionary request body construction, OAuth token acquisition, or transport calls. This preserves normal dictionary field creation while preventing internal caller wiring, tests, or future adapters from surfacing custom exception text, object representations, or credential-like payloads through internal-type string methods.

This keeps `ServiceNowClient.create_story_dictionary_field()` fail-closed before constructing `sys_dictionary` writes from unsafe `internal_type` objects.

Verification:

- Added 1 failing-first ServiceNow dictionary internal-type string-subclass test proving a hostile `str` subclass raised `RuntimeError` from overridden `strip()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_dictionary_internal_type_str_subclass -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from overridden `strip()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_dictionary_internal_type_str_subclass tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_dictionary_internal_type_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_dictionary_internal_type_before_request tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_dictionary_internal_type_before_request tests/test_servicenow.py::test_servicenow_client_creates_story_dictionary_field -q`: 5 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 179 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 651 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2625 passed, total coverage 93.39%.
