# Sprint 219 Change Log

Scope: Production hardening - admin artifact reference path redaction.

## Changes

- Added regression coverage for `GET /jobs/{job_id}/artifacts` returning an artifact reference path with URL credentials and a sensitive `client_secret` query value.
- Redacted artifact reference paths with the shared diagnostic redactor before returning them from the admin job artifact API.
- Preserved normal DB artifact paths such as `db://artifact_blobs/1`.
- Documented that artifact reference paths are diagnostic strings and are redacted before being returned.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_job_artifacts_redacts_sensitive_reference_paths tests/test_runtime.py::test_job_artifacts_lists_only_refs_for_requested_job -q` - 2 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 293 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1529 passed, 93.97% coverage.
