# Sprint 461 Change Log

## ServiceNow response non-finite JSON rejection

Hardened the ServiceNow transport response boundary so upstream response bodies containing
non-standard JSON numeric constants such as `NaN`, `Infinity`, or `-Infinity` cannot enter runtime
state as Python float values. Python `json.loads()` accepts those constants by default, which meant a
malformed ServiceNow response, proxy response, or test transport could preserve non-finite values
after the body-size and UTF-8 gates.

Successful ServiceNow responses now parse through a strict JSON loader. Non-finite constants fail
with the existing fixed `ServiceNow API response body is not valid JSON` diagnostic, without echoing
upstream field names, credential-like keys, or response values.

HTTP error responses now use the same strict parser for structured JSON diagnostics. Plain-text
error bodies are still preserved through the bounded non-JSON diagnostic path, but JSON-looking
error bodies containing non-finite constants are reduced to the fixed
`ServiceNow API error response body is not valid JSON` diagnostic instead of preserving `NaN`,
submitted field names, credential-like keys, or upstream fragments.

## Verification

- Added 2 failing-first ServiceNow urllib transport tests covering strict non-finite JSON rejection
  for successful response bodies and HTTP error response bodies.
- `python3 -m pytest tests/test_servicenow.py::test_urllib_transport_rejects_non_finite_success_json_without_body_leak tests/test_servicenow.py::test_urllib_transport_rejects_non_finite_http_error_json_without_body_leak -q`:
  failed before implementation because `NaN` reached runtime response payloads.
- `python3 -m pytest tests/test_servicenow.py::test_urllib_transport_rejects_non_finite_success_json_without_body_leak tests/test_servicenow.py::test_urllib_transport_rejects_non_finite_http_error_json_without_body_leak tests/test_servicenow.py::test_urllib_transport_rejects_malformed_success_json_without_body_leak tests/test_servicenow.py::test_urllib_transport_returns_json_body_for_http_error_response tests/test_servicenow.py::test_urllib_transport_preserves_non_json_http_error_body tests/test_servicenow.py::test_urllib_transport_truncates_large_json_http_error_strings -q`:
  6 tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 535 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2363 total tests passed at 93.83% coverage.
