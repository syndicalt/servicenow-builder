# Sprint 1046 Change Log - Worker fulfillment runtime-role validation order

## Summary

Sprint 1046 continued production hardening by tightening startup validation order for worker fulfillment. `process_one_runtime_fulfillment()` previously checked `settings.runtime_role == "api"` before calling `validate_runtime_settings()`, and `validate_runtime_settings()` previously returned early for development settings before exact-string validating the runtime role. Direct `RuntimeSettings` runtime-role string subclasses could therefore execute equality behavior before the shared runtime-role boundary owned the decision.

## Security

- `validate_runtime_settings()` now validates `RuntimeSettings.runtime_role` before returning for non-production environments.
- `process_one_runtime_fulfillment()` now calls `validate_runtime_settings()` before checking whether the runtime role is `api`.
- Direct runtime-role string subclasses and non-string objects fail with `JEDI_RUNTIME_ROLE must be a string runtime setting` before worker fulfillment API-role branching.
- The guard runs before store opening, ServiceNow client construction, transport requests, or runtime-role equality hooks.

## Tests

- Added 1 failing-first worker fulfillment startup-order assertion: `test_process_one_runtime_fulfillment_validates_runtime_role_before_api_role_branch`.
- Re-ran focused API-role rejection and production-settings-before-store-open tests after the ordering change.
- Added documentation coverage: `test_sprint_1046_documents_worker_fulfillment_runtime_role_validation_order`.

## Verification

- Focused tests failed before implementation because worker fulfillment executed a runtime-role string-subclass equality hook before validation.
- Focused startup-order and existing role tests passed after implementation.
