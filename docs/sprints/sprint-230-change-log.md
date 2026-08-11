# Sprint 230 Change Log

Scope: Production hardening - bounded admin job diagnostic identifiers.

## Changes

- Added regression coverage that oversized admin diagnostic job ids are rejected before operational-store lookup.
- Added regression coverage that URL-decoded control characters in admin diagnostic job ids are rejected before operational-store lookup.
- Added a 256-character printable ASCII boundary for externally supplied job ids on `/jobs/{job_id}/artifacts` and `/jobs/{job_id}/events`.
- Documented the admin diagnostic job-id validation rule in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_job_artifacts_rejects_oversized_job_id_before_store_lookup tests/test_runtime.py::test_job_events_rejects_control_character_job_id_before_store_lookup -q` - 2 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 304 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1568 passed, 93.89% coverage.
