# Sprint 809 Change Log - Scoped combined production exception flag

## Scope

Tightened the combined-production exception so split production services cannot carry a stale or
irrelevant `JEDI_ALLOW_COMBINED_PRODUCTION=true` flag.

## Tests First

- Added 2 failing-first split-role exception flag assertions:
  `tests/test_runtime.py::test_validate_runtime_settings_rejects_combined_production_opt_in_on_split_roles`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_809_documents_scoped_combined_production_exception_flag`.
- Initial failures proved `api` and `worker` production roles accepted the combined-role exception
  flag even though they do not need it.

## Changes

- `validate_runtime_settings()` now rejects `JEDI_ALLOW_COMBINED_PRODUCTION=true` unless
  `JEDI_RUNTIME_ROLE=combined`.
- The exception flag remains available for explicitly accepted combined production deployments.
- Split production role configurations stay cleaner and easier to audit.
- Updated the operator guide to document the scoped exception behavior.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "combined_production_opt_in_on_split_roles or combined_role_in_production"`: 4 passed, 354 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_809 or sprint_808"`: 2 passed, 880 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 358 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3214 passed, 93.37% coverage.
