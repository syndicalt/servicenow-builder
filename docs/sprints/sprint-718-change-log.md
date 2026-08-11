# Sprint 718 Change Log - ServiceNow transport timeout boundary

## Scope

Hardened direct ServiceNow urllib transport construction so `timeout_seconds` must be an exact,
finite, positive, bounded numeric value before it can reach `opener.open()`.

## Tests First

- Added 2 failing-first ServiceNow transport timeout assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_timeout_int_subclass_before_open`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_non_finite_timeout_before_open`
- Initial failures proved integer-subclass and non-finite timeout values reached opener execution.
  The hostile integer subclass fixture carried `client_secret=servicenow-timeout-float-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_718_documents_servicenow_transport_timeout_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `MAX_SERVICENOW_TRANSPORT_TIMEOUT_SECONDS` with a 300-second direct transport timeout cap.
- Added `_servicenow_transport_timeout_seconds()` to accept only exact integer or float values that
  are finite, greater than zero, and no more than 300 seconds.
- `UrllibTransport.__init__()` now validates `timeout_seconds` before storing it for opener
  execution.
- Malformed timeout values fail before network execution or credential-bearing numeric hooks can
  execute.
- Documented the ServiceNow transport timeout boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "timeout_int_subclass or non_finite_timeout"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_718` failed first with 1 failure.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q -k "timeout_int_subclass or non_finite_timeout or encodes_query_and_form_body or handles_request_without_params_or_body"`
  passed with 4 tests and 266 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_718` passed with 1 test and 791
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 270 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3027 tests and 93.32% total coverage.
