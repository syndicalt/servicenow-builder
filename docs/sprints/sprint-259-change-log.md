# Sprint 259 Change Log - ServiceNow Successful Response Body Bound

## Summary

- ServiceNow successful response body bounds prevent large upstream success payloads from being read and parsed without a size limit.
- Added a transport regression proving oversized successful response bodies raise `ServiceNowApiError` before JSON parsing.
- Updated `UrllibTransport` to read at most 10 MiB plus one sentinel byte from successful responses and reject bodies that exceed the cap.
- Updated the existing fake urllib response test helper to support the normal `read(n)` response interface.
- Documented the successful response body cap in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_urllib_transport_encodes_query_and_form_body tests/test_servicenow.py::test_urllib_transport_handles_request_without_params_or_body tests/test_servicenow.py::test_urllib_transport_rejects_oversized_success_response_body tests/test_servicenow.py::test_urllib_transport_returns_json_body_for_http_error_response tests/test_servicenow.py::test_urllib_transport_truncates_large_non_json_http_error_body tests/test_servicenow.py::test_urllib_transport_truncates_large_json_http_error_strings -q` - 6 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py` - all checks passed.
- `python3 -m pytest tests/test_servicenow.py::test_urllib_transport_encodes_query_and_form_body tests/test_servicenow.py::test_urllib_transport_handles_request_without_params_or_body tests/test_servicenow.py::test_urllib_transport_rejects_oversized_success_response_body tests/test_servicenow.py::test_urllib_transport_returns_json_body_for_http_error_response tests/test_servicenow.py::test_urllib_transport_truncates_large_non_json_http_error_body tests/test_servicenow.py::test_urllib_transport_truncates_large_json_http_error_strings tests/test_project_docs.py::test_sprint_two_hundred_fifty_nine_documents_servicenow_success_body_bound -q` - 7 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - all checks passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 174 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 333 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1650 passed, total coverage 93.95%.
