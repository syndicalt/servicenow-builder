# Sprint 806 Change Log - API build-claim role boundary

## Scope

Hardened runtime role validation so the public API role cannot carry the worker-side build-claim
mutation switch.

## Tests First

- Added 1 failing-first API build-claim role assertion:
  `tests/test_runtime.py::test_validate_runtime_settings_rejects_build_claim_apply_on_api_role`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_806_documents_api_build_claim_role_boundary`.
- Initial failure proved `JEDI_RUNTIME_ROLE=api` accepted `JEDI_BUILD_CLAIM_APPLY=true` in
  production validation.

## Changes

- `_api_runtime_role_errors()` now rejects `JEDI_BUILD_CLAIM_APPLY=true` when
  `JEDI_RUNTIME_ROLE=api`.
- The public API role continues to own lifecycle webhook and admin HTTP surfaces only.
- The worker role remains the owner of build-claim mutation, fulfillment, model execution, and
  Update Set handoff behavior.
- Documented the worker-only build-claim boundary next to the existing worker-only model,
  public-web, and Update Set apply settings.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "build_claim_apply_on_api_role or api_role_does_not_require_model_provider"`: 2 passed, 351 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 353 passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_806`: 1 passed, 878 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3206 passed, 93.36% coverage.
