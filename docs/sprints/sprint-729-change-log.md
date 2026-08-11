# Sprint 729 Change Log - ServiceNow transport JSON encoding cause boundary

## Scope

Hardened ServiceNow urllib transport JSON request-body diagnostics so malformed JSON payload
failures do not retain unsafe validator or serializer exceptions as public `ServiceNowApiError`
causes.

## Tests First

- Added 3 failing-first ServiceNow transport JSON encoding cause assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_non_finite_json_request_body_without_sending`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_json_body_string_subclass_key_before_serialization`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_json_body_non_json_value_before_serialization`
- Initial failures proved the public `ServiceNowApiError` retained internal causes for:
  - `bad_score` non-finite numeric payload rejection.
  - `HostileJsonBodyKey` unsupported key rejection.
  - `HostileJsonBodyValue` unsupported value rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_729_documents_servicenow_transport_json_encoding_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original `ValueError` causes when non-finite JSON request bodies are rejected.
- Suppressed original `TypeError` causes when unsupported JSON keys or values are rejected.
- Preserved the existing fixed diagnostics:
  - `ServiceNow JSON request body contains non-finite numeric values`
  - `ServiceNow JSON request body contains non-JSON values`
- Documented the ServiceNow transport JSON encoding cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "non_finite_json_request_body or json_body_string_subclass_key or json_body_non_json_value"`
  failed first with 3 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_729` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "non_finite_json_request_body or json_body_string_subclass_key or json_body_non_json_value or circular_json_body or deep_json_body or sends_json_body"`
  passed with 5 tests and 283 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_729` passed with 1 test and 802
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 288 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3056 tests and 93.33% total coverage.
