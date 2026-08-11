# Sprint 587 Change Log

## ServiceNow HTTP error diagnostic string-subclass guard

Sprint 587 continued production hardening by preventing parsed HTTP error diagnostic shaping from accepting string subclasses as primitive text. `_bound_http_error_diagnostics()` already bounded dictionaries, lists, and tuples before response handling continued, and exact string values still use the existing truncation path, but a Python transport could provide a `str` subclass inside parsed `HttpResponse.json_body` and have it reflected as normal diagnostic text.

Parsed HTTP error diagnostic shaping now accepts exact `str` values only for string truncation. String subclasses render as `[non-json value]` before truncation, response propagation, ServiceNow API exception formatting, work-note failure reporting, artifact references, or operator-log output.

This keeps transport-level HTTP error diagnostics useful while ensuring alternate transports cannot inject subclass behavior, object type names, object string output, upstream body fragments, or credential-like payloads into parsed error diagnostics.

Verification:

- Added 1 failing-first ServiceNow HTTP error diagnostic string-subclass test proving a subclassed parsed error `message` was reflected before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_rejects_string_subclass_values -q`: failed before implementation because the subclassed parsed HTTP error message appeared in the diagnostic instead of `[non-json value]`.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_rejects_string_subclass_values tests/test_servicenow.py::test_bound_http_error_diagnostics_does_not_consume_all_fields_for_wide_payload tests/test_servicenow.py::test_urllib_transport_truncates_large_json_http_error_strings -q`: 3 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_587_documents_servicenow_http_error_diagnostic_str_subclass_guard -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 190 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 661 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2646 passed, 93.36% coverage.
