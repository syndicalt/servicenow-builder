# Sprint 698 Change Log - ServiceNow CICD probe response boundary

## Scope

Hardened `ServiceNowClient.probe_cicd_update_set_endpoint()` so observational CI/CD Update Set probe
responses validate transport object, status code, and response body shape before returning operator
diagnostic data.

## Tests First

- Added 6 failing-first ServiceNow CICD probe response assertions:
  - `tests/test_servicenow.py::test_servicenow_cicd_probe_rejects_response_object_without_leak`
  - `tests/test_servicenow.py::test_servicenow_cicd_probe_rejects_status_code_object_without_leak`
  - `tests/test_servicenow.py::test_servicenow_cicd_probe_rejects_status_code_outside_http_range[99]`
  - `tests/test_servicenow.py::test_servicenow_cicd_probe_rejects_status_code_outside_http_range[600]`
  - `tests/test_servicenow.py::test_servicenow_cicd_probe_rejects_body_object_without_leak`
  - `tests/test_servicenow.py::test_servicenow_cicd_probe_rejects_body_dict_subclass_without_leak`
- Initial failures proved malformed probe responses could raise or leak through raw attribute
  access, unvalidated status values, and unsafe body copying with
  `client_secret=servicenow-probe-response-object-secret`,
  `client_secret=servicenow-probe-status-code-secret`,
  `client_secret=servicenow-probe-body-secret`, or
  `client_secret=servicenow-probe-dict-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_698_documents_servicenow_cicd_probe_response_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_probe_response_body()` for observational probe response shaping.
- The probe now uses the shared exact response/status validator before reading status or body fields.
- Probe response bodies must be exact dictionaries before copying.
- Valid HTTP error statuses remain returned as probe data instead of raising, preserving the
  endpoint-probe workflow.
- Documented the ServiceNow CICD probe response boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_cicd_probe_rejects_response_object_without_leak or servicenow_cicd_probe_rejects_status_code_object_without_leak or servicenow_cicd_probe_rejects_status_code_outside_http_range or servicenow_cicd_probe_rejects_body_object_without_leak or servicenow_cicd_probe_rejects_body_dict_subclass_without_leak"`
  failed first with 6 failures.
- `python3 -m pytest tests/test_servicenow.py -q -k "servicenow_client_probes_cicd_update_set_endpoint_without_state_change or servicenow_cicd_probe_rejects_response_object_without_leak or servicenow_cicd_probe_rejects_status_code_object_without_leak or servicenow_cicd_probe_rejects_status_code_outside_http_range or servicenow_cicd_probe_rejects_body_object_without_leak or servicenow_cicd_probe_rejects_body_dict_subclass_without_leak"`
  passed, 7 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_698`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_697 or sprint_698"` passed,
  2 tests.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 236 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2973 tests with 93.26% total coverage.
