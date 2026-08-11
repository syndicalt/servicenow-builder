# Sprint 595 Change Log

## ServiceNow HTTP diagnostic exact truncation cap

Sprint 595 continued production hardening by tightening ServiceNow HTTP diagnostic truncation so the configured cap is the total diagnostic length, including the `...[truncated]` marker. `_truncate_http_error_diagnostic()` previously retained `MAX_HTTP_ERROR_DIAGNOSTIC_CHARS` characters and then appended the marker, which allowed oversized diagnostics to exceed the configured maximum by the marker length.

The shared truncation helper now reserves marker space inside `MAX_HTTP_ERROR_DIAGNOSTIC_CHARS` before appending the marker. Transport plain-text HTTP error bodies, parsed JSON HTTP error strings, and final ServiceNow API exception diagnostics all continue to use the same helper, so the exact cap invariant is enforced at the common boundary.

This keeps operator logs, work notes, and artifact diagnostics aligned with the configured diagnostic maximum instead of relying on a near-cap behavior.

Verification:

- Added 1 failing-first ServiceNow HTTP diagnostic exact-cap test proving `_truncate_http_error_diagnostic()` returned 4110 characters for a 4096-character cap before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_truncate_http_error_diagnostic_keeps_marker_inside_configured_cap -q`: failed before implementation with length 4110 instead of 4096.
- `python3 -m pytest tests/test_servicenow.py::test_truncate_http_error_diagnostic_keeps_marker_inside_configured_cap tests/test_servicenow.py::test_urllib_transport_truncates_large_non_json_http_error_body tests/test_servicenow.py::test_urllib_transport_truncates_large_json_http_error_strings tests/test_servicenow.py::test_servicenow_api_failure_bounds_final_error_diagnostic -q`: 4 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_595_documents_servicenow_http_diagnostic_exact_truncation_cap -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 198 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 669 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2662 passed, 93.19% coverage.
