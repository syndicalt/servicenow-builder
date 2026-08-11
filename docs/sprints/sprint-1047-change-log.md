# Sprint 1047 Change Log - Embedded worker runtime mode exact-string boundary

## Summary

Sprint 1047 continued production hardening by tightening embedded runtime worker mode checks. Direct `run_once()` and `run_loop()` callers could pass `RuntimeSettings` objects with string-subclass runtime role or environment values and reach equality checks before the shared exact-string runtime setting boundary.

## Security

- `run_once()` now validates `RuntimeSettings.runtime_role` through the shared runtime-role validator before checking whether the role is `api`.
- `_validate_run_loop_controls()` now validates `RuntimeSettings.runtime_environment` through the shared runtime-environment validator before enforcing production `JEDI_WORKER_STOP_ON_FAILURE=false`.
- Malformed runtime role and environment direct objects fail with setting-name `RuntimeConfigError` diagnostics before worker role branching or production stop-on-failure checks.
- The guard runs before processor calls, maintenance pruner calls, stale-job recovery calls, alert emitters, store work, or sleep calls.

## Tests

- Added 2 failing-first embedded worker direct-object assertions:
  `test_run_once_validates_runtime_role_before_api_role_branch` and
  `test_run_loop_validates_runtime_environment_before_stop_on_failure_branch`.
- Re-ran focused existing worker API-role and direct-control validation tests after implementation.
- Added documentation coverage: `test_sprint_1047_documents_embedded_worker_runtime_mode_exact_string_boundary`.

## Verification

- Focused tests failed before implementation because embedded worker paths executed runtime role and environment string-subclass equality hooks before validation.
- Focused worker boundary and existing direct-control tests passed after implementation.
