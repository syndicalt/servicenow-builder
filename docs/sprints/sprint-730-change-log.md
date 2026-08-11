# Sprint 730 Change Log - ServiceNow transport successful-response JSON parse cause boundary

## Scope

Hardened ServiceNow urllib transport successful-response JSON parse diagnostics so invalid response
body failures do not retain unsafe decoder or parser exceptions as public `ServiceNowApiError`
causes.

## Tests First

- Added 3 failing-first ServiceNow successful-response JSON parse cause assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_invalid_utf8_success_response_without_body_leak`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_malformed_success_json_without_body_leak`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_non_finite_success_json_without_body_leak`
- Initial failures proved the public `ServiceNowApiError` retained internal causes for:
  - `access_token` invalid UTF-8 response body rejection.
  - `client_secret` malformed JSON response body rejection.
  - `score` non-finite JSON response body rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_730_documents_servicenow_transport_success_json_parse_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original `UnicodeDecodeError` causes when successful response bodies are not valid
  UTF-8 JSON.
- Suppressed original `JSONDecodeError` and non-finite JSON `ValueError` causes when successful
  response bodies are not valid JSON.
- Preserved the existing fixed diagnostics:
  - `ServiceNow API response body is not valid UTF-8 JSON`
  - `ServiceNow API response body is not valid JSON`
- Documented the ServiceNow transport successful-response JSON parse cause boundary in the operator
  guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "invalid_utf8_success_response or malformed_success_json or non_finite_success_json"`
  failed first with 3 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_730` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "invalid_utf8_success_response or malformed_success_json or non_finite_success_json or rejects_success_body_bytes_subclass"`
  passed with 4 tests and 284 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_730` passed with 1 test and 803
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 288 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3057 tests and 93.33% total coverage.
