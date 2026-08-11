# Sprint 1058 Change Log - Trusted Host Worker Role Boundary

## Scope

Production hardening for split runtime configuration hygiene. `JEDI_TRUSTED_HOSTS`
is a public API Host header control and should not be configured on worker-only
services.

## Changes

- Extended worker-role production validation to reject `JEDI_TRUSTED_HOSTS`.
- Updated the existing worker/API boundary regression so API-only lifecycle,
  admin, and trusted-host settings fail together on `JEDI_RUNTIME_ROLE=worker`.
- Documented that trusted-host allowlists belong only on `api` or intentionally
  combined runtime services.

## Tests

- `test_validate_runtime_settings_rejects_api_secrets_on_worker_role`
- `test_sprint_1058_documents_trusted_host_worker_boundary`

## Residual Risk

This prevents API Host policy from drifting into worker-only services. It
does not replace edge controls; production still needs TLS termination, WAF,
request-size enforcement, and distributed rate limiting at the approved hosting
boundary.
