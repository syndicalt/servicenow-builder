# Sprint 699 Change Log - ServiceNow API error formatter prevalidated-status boundary

## Scope

Hardened the internal ServiceNow API error formatter so it requires callers to provide the
prevalidated integer status code produced by the shared response/status boundary.

## Tests First

- Added 2 failing-first ServiceNow API error-formatter assertions:
  - `tests/test_servicenow.py::test_servicenow_api_error_message_requires_validated_status_code`
  - `tests/test_servicenow.py::test_servicenow_api_error_message_does_not_read_hostile_status_fallback`
- Initial failures proved `_servicenow_api_error_message()` accepted missing `status_code` and could
  fall back to `response.status_code`, allowing hostile status objects to raise
  `client_secret=servicenow-error-status-secret` through string formatting.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_699_documents_servicenow_api_error_status_prevalidation`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `_servicenow_api_error_message()` now fails closed unless `status_code` is supplied.
- The formatter no longer falls back to `response.status_code`.
- Existing ServiceNow API error paths continue to pass the integer returned by the shared exact
  response/status validator.
- Documented the ServiceNow API error formatter status prevalidation boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_api_error_message_requires_validated_status_code or servicenow_api_error_message_does_not_read_hostile_status_fallback"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_api_error_message_requires_validated_status_code or servicenow_api_error_message_does_not_read_hostile_status_fallback or servicenow_api_failure_raises_without_secret_leakage or servicenow_api_error_body_dict_subclass_collapses_without_leak or servicenow_table_api_rejects_status_code_outside_http_range"`
  passed, 6 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_699`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_698 or sprint_699"` passed,
  2 tests.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 238 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2976 tests with 93.26% total coverage.
