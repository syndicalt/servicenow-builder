# Sprint 602 Change Log

## ServiceNow HTTP error diagnostic text normalization

Sprint 602 continued production hardening by normalizing exact string values and keys inside parsed ServiceNow HTTP error diagnostics before they leave the transport boundary. `_bound_http_error_diagnostics()` already bounded collection traversal, handled cycles, rejected string subclasses, normalized non-JSON scalar values, and applied the shared exact-length cap, but exact strings could still retain raw newline or tab characters in structured transport diagnostics.

The HTTP diagnostic bounding path now collapses whitespace/control-character runs for exact string values and exact string keys before applying `_truncate_http_error_diagnostic()`. This keeps lower-level transport diagnostics useful while preventing malformed upstream HTTP error responses from injecting raw multiline diagnostic text into runtime errors, work notes, artifacts, or operator logs.

Verification:

- Added 2 failing-first ServiceNow HTTP error diagnostic text-normalization tests proving `_bound_http_error_diagnostics()` preserved newline and tab characters in exact string values and keys before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_normalizes_exact_string_values tests/test_servicenow.py::test_bound_http_error_diagnostics_normalizes_exact_string_keys -q`: failed before implementation because parsed HTTP diagnostic strings retained raw newline and tab characters.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_normalizes_exact_string_values tests/test_servicenow.py::test_bound_http_error_diagnostics_normalizes_exact_string_keys tests/test_servicenow.py::test_bound_http_error_diagnostics_rejects_string_subclass_values tests/test_servicenow.py::test_bound_http_error_diagnostics_normalizes_non_json_scalar_values -q`: 4 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_602_documents_servicenow_http_error_diagnostic_text_normalization -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 209 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 676 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2680 passed, total coverage 93.16%, required 90% coverage reached.
