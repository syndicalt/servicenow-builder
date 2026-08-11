# Sprint 590 Change Log

## ServiceNow HTTP error diagnostic scalar normalization

Sprint 590 continued production hardening by preventing parsed HTTP error diagnostic shaping from reflecting unsupported scalar values before payloads leave the transport. `_bound_http_error_diagnostics()` already bounded traversal, projected unsafe keys, guarded string subclasses, and truncated exact strings, but arbitrary non-string objects and non-finite floats were still returned directly.

Parsed HTTP error diagnostic shaping now normalizes scalar values through a JSON-safe boundary. `None`, booleans, integers, finite floats, and exact strings remain available for diagnostics. Non-finite floats, arbitrary Python objects, bytes, and other unsupported scalar values render as `[non-json value]` without calling `str()` or `repr()` on the original value.

This keeps transport-level HTTP error diagnostics useful while ensuring alternate transports cannot inject object type names, object string output, non-finite numeric tokens, upstream value fragments, or credential-like payloads into parsed error diagnostics before ServiceNow API exception handling sees them.

Verification:

- Added 1 failing-first ServiceNow HTTP error diagnostic scalar normalization test proving an unsupported object `repr()` and `nan` were reflected before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_normalizes_non_json_scalar_values -q`: failed before implementation because the hostile object representation and `nan` value appeared in the parsed HTTP error diagnostic instead of `[non-json value]`.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_normalizes_non_json_scalar_values tests/test_servicenow.py::test_bound_http_error_diagnostics_rejects_non_json_keys tests/test_servicenow.py::test_bound_http_error_diagnostics_rejects_string_subclass_values tests/test_servicenow.py::test_bound_http_error_diagnostics_does_not_consume_all_fields_for_wide_payload -q`: 4 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_590_documents_servicenow_http_error_diagnostic_scalar_normalization -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 193 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 664 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2652 passed, 93.34% coverage.
