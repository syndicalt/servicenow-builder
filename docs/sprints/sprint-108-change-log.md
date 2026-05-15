# Sprint 108 Change Log

## Goal

Harden runtime configuration and secret posture so production deployments fail closed when required authentication or model settings are missing.

## Changes

- Added `validate_runtime_settings()` as the explicit production startup/runtime guard.
- Wired the API runtime through validation before it opens the operational store.
- Wired the worker fulfillment path through validation before it opens the operational store or creates outbound clients.
- Required `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256` and `JEDI_LIFECYCLE_WEBHOOK_SECRET` for production.
- Rejected `JEDI_ADMIN_AUTH_MODE=disabled` and `JEDI_ADMIN_AUTH_MODE=dev_basic` for production API startup.
- Kept reserved production admin modes fail-closed until `oidc` or `servicenow_oauth` is fully implemented.
- Required `JEDI_MODEL_PROVIDER=openai`, `OPENAI_API_KEY`, and `OPENAI_MODEL` for production worker execution.
- Added a production fail-closed checklist and secret inventory to the operator guide.
- Corrected the production-hardening backlog to reflect the actual Sprint 106, Sprint 107, and Sprint 108 work.

## Tests

- Added runtime validation tests for production webhook auth, admin auth, and model-provider secrets.
- Added API and worker tests proving invalid production settings are rejected before store access.
- Added documentation tests for the production checklist, secret inventory, backlog correction, and this sprint log.

## Decision

Development remains permissive enough for PDI/Railway iteration, but production now has an explicit fail-closed boundary. This is intentionally strict: the current reserved admin auth modes are documented but not production-enabled, so a production API should not start with a pretend admin-auth posture.
