# Sprint 1056 Change Log - Lifecycle Webhook Secret Rotation

## Scope

Production hardening for lifecycle webhook credential rotation. The API now supports
an explicit overlap window so ServiceNow lifecycle emitters can move from an old
signing secret to a new signing secret without dropping valid events during the
cutover.

## Changes

- Added `JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET` to the runtime settings model,
  `.env.example`, production validation, API construction, and runtime redaction.
- Updated lifecycle webhook HMAC and shared-secret authentication to accept the
  active secret or previous secret during a rotation window while preserving
  malformed-header rejection before constant-time comparison.
- Added production validation that rejects weak, oversized, whitespace-bearing,
  control-character-bearing, or duplicate previous lifecycle webhook secrets.
- Kept lifecycle webhook secrets API-only by extending worker-role production
  validation to reject `JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET`.
- Documented the lifecycle webhook secret rotation runbook in
  `docs/operator-guide.md`, including verification evidence and previous-secret
  retirement.

## Tests

- `test_lifecycle_webhook_hmac_auth_accepts_previous_secret_during_rotation`
- `test_lifecycle_webhook_hmac_auth_rejects_unknown_secret_during_rotation`
- `test_lifecycle_webhook_shared_secret_accepts_previous_secret_during_rotation`
- `test_load_runtime_settings_reads_lifecycle_webhook_hmac_config`
- `test_load_runtime_settings_rejects_malformed_lifecycle_webhook_previous_secret`
- `test_validate_runtime_settings_rejects_duplicate_lifecycle_webhook_rotation_secret`
- `test_validate_runtime_settings_rejects_weak_lifecycle_webhook_previous_secret`
- `test_validate_runtime_settings_rejects_api_secrets_on_worker_role`
- `test_sprint_1056_documents_lifecycle_webhook_secret_rotation`

## Residual Risk

This sprint provides overlap rotation for lifecycle webhook signing secrets only.
Admin tokens, ServiceNow OAuth client secrets, model provider keys, and alert webhook
credentials still require coordinated secret-manager rotation and service restart
unless a dedicated overlap mechanism is added later.
