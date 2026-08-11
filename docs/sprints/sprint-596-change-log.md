# Sprint 596 Change Log

## ServiceNow API diagnostic per-string cap

Sprint 596 continued production hardening by bounding exact string values inside ServiceNow API exception diagnostic objects before final exception formatting. `_servicenow_diagnostic_value()` already projected unsafe keys, normalized unsafe scalar values, bounded collection traversal, handled cycles, and applied a final formatted diagnostic cap, but exact string values could still remain oversized inside the intermediate structured diagnostic object before `repr()` and final truncation.

ServiceNow API diagnostic text now passes through the shared exact-length truncation helper after redaction and whitespace normalization. This keeps each exact string diagnostic value within `MAX_HTTP_ERROR_DIAGNOSTIC_CHARS`, including the `...[truncated]` marker, before it is stored in the structured diagnostic object. The existing final formatted exception cap remains in place as defense in depth.

This reduces memory pressure and keeps diagnostic shaping aligned with the operator-facing bounded-diagnostics contract before logs, work notes, and artifacts see the final formatted error.

Verification:

- Added 1 failing-first ServiceNow API diagnostic per-string cap test proving `_servicenow_diagnostic_value()` preserved an oversized message without `...[truncated]` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_diagnostic_value_caps_normalized_text_values -q`: failed before implementation because the structured diagnostic message was oversized and did not end with `...[truncated]`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_diagnostic_value_caps_normalized_text_values tests/test_servicenow.py::test_servicenow_diagnostic_value_does_not_consume_all_fields_for_wide_response tests/test_servicenow.py::test_servicenow_diagnostic_value_handles_circular_response_payload tests/test_servicenow.py::test_servicenow_api_failure_bounds_final_error_diagnostic tests/test_servicenow.py::test_servicenow_api_failure_normalizes_untrusted_error_diagnostics tests/test_servicenow.py::test_servicenow_api_failure_rejects_non_json_diagnostic_keys -q`: 6 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_596_documents_servicenow_api_diagnostic_per_string_cap -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 199 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 670 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2664 passed, 93.19% coverage.
