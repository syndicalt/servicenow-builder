# Sprint 597 Change Log

## ServiceNow diagnostic duplicate key exact cap

Sprint 597 continued production hardening by keeping duplicate rendered diagnostic keys inside the same configured cap used for ordinary ServiceNow diagnostic keys. `_servicenow_diagnostic_key()` and `_http_error_diagnostic_key()` already bounded exact string keys, but `_unique_servicenow_diagnostic_key()` appended duplicate suffixes such as ` (2)` after that cap, allowing long colliding keys to exceed `MAX_HTTP_ERROR_DIAGNOSTIC_CHARS`.

Duplicate diagnostic key rendering now reserves space for both the `...[truncated]` marker and deterministic duplicate suffix before returning the key. The shared helper is used by both parsed HTTP error diagnostic shaping and ServiceNow API exception diagnostic projection, so duplicate suffixes stay useful without escaping the bounded-diagnostic contract.

This closes a small but real auditability gap: bounded diagnostic keys now remain bounded even when hostile or unusually long response keys collapse to the same rendered label.

Verification:

- Added 2 failing-first duplicate-key cap tests proving parsed HTTP error diagnostics and ServiceNow API exception diagnostics could append ` (2)` beyond the configured key cap before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_keeps_duplicate_keys_inside_cap tests/test_servicenow.py::test_servicenow_diagnostic_value_keeps_duplicate_keys_inside_cap -q`: failed before implementation because duplicate keys exceeded `MAX_HTTP_ERROR_DIAGNOSTIC_CHARS`.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_keeps_duplicate_keys_inside_cap tests/test_servicenow.py::test_servicenow_diagnostic_value_keeps_duplicate_keys_inside_cap tests/test_servicenow.py::test_bound_http_error_diagnostics_rejects_non_json_keys tests/test_servicenow.py::test_servicenow_api_failure_rejects_non_json_diagnostic_keys tests/test_servicenow.py::test_servicenow_diagnostic_value_caps_normalized_text_values -q`: 5 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_597_documents_servicenow_diagnostic_duplicate_key_exact_cap -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 201 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 671 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2667 passed, 93.20% coverage.
