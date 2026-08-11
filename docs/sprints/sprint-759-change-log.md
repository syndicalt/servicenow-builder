# Sprint 759 Change Log - Admin not-found cause boundary

## Scope

Hardened admin not-found diagnostics so missing artifact and missing job lookups do not retain unsafe runtime-store `KeyError` exceptions as public `HTTPException` causes.

## Tests First

- Added 3 failing-first admin not-found cause assertions:
  - `tests/test_runtime.py::test_admin_artifact_api_not_found_does_not_retain_store_cause`
  - `tests/test_runtime.py::test_admin_get_job_or_404_does_not_retain_store_cause`
  - `tests/test_runtime.py::test_admin_console_artifact_not_found_does_not_retain_store_cause`
- Initial failures proved JSON artifact API, HTML admin artifact view, and job lookup 404s retained runtime-store `KeyError` values on `HTTPException.__cause__`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_759_documents_admin_not_found_cause_boundary`
- The documentation assertion was added before the sprint log and operator guide update, so the docs gate covers the new operator-facing contract.

## Changes

- Suppressed original `KeyError` causes in JSON artifact not-found responses.
- Suppressed original `KeyError` causes in HTML admin artifact not-found responses.
- Suppressed original `KeyError` causes in job not-found responses.
- Preserved fixed diagnostics:
  - `artifact not found`
  - `job not found`
- Documented the admin not-found cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "not_found_does_not_retain_store_cause or get_job_or_404_does_not_retain_store_cause"` - 3 passed, 339 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_759` - 1 passed, 832 deselected.
- `python3 -m pytest tests/test_runtime.py -q -k "artifact_read or admin_console_artifact_view"` - 19 passed, 323 deselected.
- `ruff check src tests` - passed.
- `mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3102 passed, 93.39% coverage.
