# Sprint 741 Change Log - Runtime worker report cause boundary

## Scope

Hardened runtime worker report diagnostics so stdout report rendering failures do not retain unsafe
low-level exception instances as public `ValueError` causes.

## Tests First

- Added 4 failing-first runtime worker report cause assertions:
  - `tests/test_runtime_entrypoints.py::test_runtime_report_json_rejects_non_finite_summary_without_payload_leak`
  - `tests/test_runtime_entrypoints.py::test_runtime_report_json_rejects_non_json_summary_without_payload_leak`
  - `tests/test_runtime_worker_retention.py::test_runtime_report_json_rejects_string_subclass_values_without_stringifying`
  - `tests/test_runtime_worker_retention.py::test_runtime_report_json_rejects_string_subclass_keys_without_stringifying`
- Initial failures proved the public `ValueError` retained unsafe causes for:
  - Runtime report `idle` non-finite numeric rejection.
  - Runtime report `StringifiesSecret` unsupported object rejection.
  - Runtime report `HostileRuntimeReportText` string subclass value rejection.
  - Runtime report `HostileRuntimeReportText` string subclass key rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_741_documents_runtime_worker_report_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original Pydantic serializer causes in `_runtime_report_json()`.
- Suppressed original non-finite numeric validation causes in `_runtime_report_json()`.
- Suppressed original non-JSON structure validation causes in `_runtime_report_json()`.
- Preserved the existing fixed diagnostics:
  - `runtime worker report contains non-finite numeric values`
  - `runtime worker report contains non-JSON values`
- Documented the runtime worker report cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_entrypoints.py -q -k runtime_report_json` failed first with 2
  failures.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k runtime_report_json_rejects` failed
  first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_741` failed first with 1 failure.
- `python3 -m pytest tests/test_runtime_entrypoints.py -q -k runtime_report_json` passed with 2 tests
  and 8 deselected.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k runtime_report_json_rejects` passed
  with 2 tests and 33 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_741` passed with 1 test and 814
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_runtime_entrypoints.py tests/test_runtime_worker_retention.py -q`
  passed with 45 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3071 tests and 93.33% total coverage.
