# Sprint 589 Change Log

## ServiceNow HTTP error diagnostic key projection

Sprint 589 continued production hardening by preventing parsed HTTP error diagnostic shaping from reflecting Python-specific dictionary keys before payloads leave the transport. `_bound_http_error_diagnostics()` already bounded traversal, guarded diagnostic text values, and truncated exact strings, but it still preserved raw dictionary keys.

Parsed HTTP error diagnostic shaping now projects object keys through a safe key path. Exact string keys are bounded before formatting, duplicate rendered keys receive deterministic suffixes, and non-string keys render as `[non-json key]` without calling `str()` or `repr()` on the original key.

This keeps transport-level HTTP error diagnostics useful while ensuring alternate transports cannot inject object type names, object string output, upstream key fragments, or credential-like payloads into parsed error diagnostics before ServiceNow API exception handling sees them.

Verification:

- Added 1 failing-first ServiceNow HTTP error diagnostic key projection test proving a hostile dictionary key `repr()` was reflected before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_rejects_non_json_keys -q`: failed before implementation because the hostile key representation appeared in the parsed HTTP error diagnostic instead of `[non-json key]`.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_rejects_non_json_keys tests/test_servicenow.py::test_bound_http_error_diagnostics_rejects_string_subclass_values tests/test_servicenow.py::test_bound_http_error_diagnostics_does_not_consume_all_fields_for_wide_payload -q`: 3 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_589_documents_servicenow_http_error_diagnostic_key_projection -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 192 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 663 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2650 passed, 93.33% coverage.
