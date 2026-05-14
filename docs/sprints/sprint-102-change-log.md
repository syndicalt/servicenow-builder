# Sprint 102 Change Log

## Goal

Back off the overly literal "ServiceNow role-backed admin auth" assumption and create a production-safe admin authentication strategy boundary.

## Changes

- Added `JEDI_ADMIN_AUTH_MODE` with explicit modes:
  - `disabled`
  - `dev_basic`
  - `oidc`
  - `servicenow_oauth`
- Added `JEDI_ENVIRONMENT`.
- Changed the admin console default to fail closed with `JEDI_ADMIN_AUTH_MODE=disabled`.
- Kept Basic auth available only as `dev_basic` and only when `JEDI_ENVIRONMENT=development`.
- Made reserved `oidc` and `servicenow_oauth` modes fail closed with `501 Not Implemented`.
- Documented concrete future OIDC and ServiceNow OAuth configuration details in `docs/admin-auth-config.md`.
- Added ADR 0005 documenting why the sidecar should not rely on a ServiceNow browser session cookie under SSO.

## Verification

- Added failing-first runtime tests for disabled auth, dev-only Basic auth, reserved auth modes, and runtime settings.
- Added documentation regression tests for the auth config and ADR.
- Full lint, type, and coverage gate before deployment.

## Decision

ServiceNow role-backed browser authentication is not a safe assumption under SSO. Production auth should use a customer-approved IdP OIDC integration or a fully reviewed ServiceNow OAuth authorization code flow with explicit role verification. Basic auth remains a development-only fallback.
