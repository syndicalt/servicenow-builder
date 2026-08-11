# Sprint 258 Change Log - ServiceNow HTTP Error Diagnostic Bounds

## Summary

- ServiceNow HTTP error diagnostic bounds prevent large upstream error bodies from flowing into runtime exceptions or operator diagnostics unbounded.
- Added transport regressions for large non-JSON HTTP error bodies and large string values inside JSON HTTP error bodies.
- Added recursive diagnostic bounding in the ServiceNow HTTP error-body normalizer so short structured errors remain intact while large strings receive a truncation marker.
- Verified existing HTTP-error JSON parsing, non-JSON preservation, and secret-redaction behavior still pass.
- Documented that ServiceNow HTTP error diagnostics are bounded at the transport boundary.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_urllib_transport_returns_json_body_for_http_error_response tests/test_servicenow.py::test_urllib_transport_preserves_non_json_http_error_body tests/test_servicenow.py::test_urllib_transport_truncates_large_non_json_http_error_body tests/test_servicenow.py::test_urllib_transport_truncates_large_json_http_error_strings tests/test_servicenow.py::test_servicenow_api_failure_raises_without_secret_leakage tests/test_servicenow.py::test_redact_secrets_masks_sensitive_values -q` - 14 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py` - all checks passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success with 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 332 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1648 passed with 93.95% total coverage.
