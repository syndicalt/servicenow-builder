# Sprint 260 Change Log - ServiceNow HTTP Error Body Read Bound

## Summary

- ServiceNow HTTP error response reads now use the same 10 MiB plus one sentinel byte cap as successful response reads.
- Added a failing transport regression proving the HTTP error path no longer calls `read(-1)` for oversized upstream error bodies.
- Updated `UrllibTransport` to return a compact oversized-body diagnostic when an HTTP error response exceeds the cap before JSON parsing or diagnostic truncation.
- Preserved existing useful diagnostics for smaller JSON and non-JSON HTTP error responses.
- Documented the HTTP error response read cap in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_urllib_transport_returns_json_body_for_http_error_response tests/test_servicenow.py::test_urllib_transport_preserves_non_json_http_error_body tests/test_servicenow.py::test_urllib_transport_truncates_large_non_json_http_error_body tests/test_servicenow.py::test_urllib_transport_truncates_large_json_http_error_strings tests/test_servicenow.py::test_urllib_transport_bounds_oversized_http_error_response_body tests/test_servicenow.py::test_urllib_transport_rejects_oversized_success_response_body -q` - 6 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/servicenow.py tests/test_servicenow.py` - success: no issues found in 2 source files.
- `python3 -m pytest tests/test_servicenow.py::test_urllib_transport_returns_json_body_for_http_error_response tests/test_servicenow.py::test_urllib_transport_preserves_non_json_http_error_body tests/test_servicenow.py::test_urllib_transport_truncates_large_non_json_http_error_body tests/test_servicenow.py::test_urllib_transport_truncates_large_json_http_error_strings tests/test_servicenow.py::test_urllib_transport_bounds_oversized_http_error_response_body tests/test_servicenow.py::test_urllib_transport_rejects_oversized_success_response_body tests/test_project_docs.py::test_sprint_two_hundred_sixty_documents_servicenow_http_error_body_read_bound -q` - 7 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - all checks passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 334 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1652 passed, total coverage 93.95%.
