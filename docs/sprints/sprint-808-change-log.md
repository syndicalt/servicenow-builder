# Sprint 808 Change Log - Combined production explicit opt-in

## Scope

Hardened hosted production validation so the local-development `combined` runtime role cannot be
used in production without an explicit deployment-owner opt-in.

## Tests First

- Added 2 failing-first combined production assertions in `tests/test_runtime.py`:
  - `test_validate_runtime_settings_rejects_combined_role_in_production_without_explicit_opt_in`
  - `test_validate_runtime_settings_allows_combined_role_in_production_with_explicit_opt_in`
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_808_documents_combined_production_explicit_opt_in`.
- Initial failure proved a fully configured `JEDI_RUNTIME_ROLE=combined` production runtime could
  pass validation without a conscious exception flag.

## Changes

- Added `JEDI_ALLOW_COMBINED_PRODUCTION`, defaulting to `false`.
- `validate_runtime_settings()` now rejects `JEDI_RUNTIME_ROLE=combined` in production unless
  `JEDI_ALLOW_COMBINED_PRODUCTION=true`.
- Split `api` and `worker` services remain the production target.
- Updated `.env.example` and the operator guide to document the exception flag and its risk.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "combined_role_in_production"`: 2 passed, 354 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_808`: 1 passed, 880 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 356 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3211 passed, 93.37% coverage.
