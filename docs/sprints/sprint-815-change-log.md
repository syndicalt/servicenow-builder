# Sprint 815 Change Log - Production stale-job threshold ceiling validation

## Scope

Hardened production stale running job detection settings so an excessive threshold cannot silently
disable stale-job visibility for days.

## Tests First

- Added 1 failing-first stale-job threshold assertion:
  `tests/test_runtime.py::test_validate_runtime_settings_rejects_excessive_production_stale_threshold`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_815_documents_production_stale_job_threshold_ceiling`.
- Initial failure proved production worker validation accepted a seven-day
  `JEDI_RUNNING_JOB_STALE_AFTER_SECONDS` threshold through direct `RuntimeSettings`.

## Changes

- `JEDI_RUNNING_JOB_STALE_AFTER_SECONDS` now has a production ceiling of `86400`.
- Diagnostics name the setting and ceiling without echoing the oversized configured value.
- Updated the operator guide to document the production stale-job threshold ceiling.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "excessive_production_stale_threshold or non_positive_stale_threshold"`: 2 passed, 365 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_815`: 1 passed, 887 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 367 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3229 passed, 93.38% coverage.
