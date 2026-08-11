# Sprint 1057 Change Log - Runtime Trusted Host Enforcement

## Scope

Production hardening for public runtime Host header handling. The API can now enforce a
deployment-owned Host allowlist in-process instead of relying only on the hosting edge or proxy.

## Changes

- Added `JEDI_TRUSTED_HOSTS` to runtime settings and `.env.example`.
- Added production startup validation requiring trusted hosts for public `api` and `combined`
  runtime roles.
- Rejected malformed production trusted-host entries including wildcard-all entries, padded
  values, schemes, paths, control characters, invalid ports, and local wildcard domains.
- Installed Starlette `TrustedHostMiddleware` when trusted hosts are configured.
- Documented the trusted-host production deployment contract in `docs/operator-guide.md`.

## Tests

- `test_load_runtime_settings_reads_trusted_hosts`
- `test_validate_runtime_settings_rejects_production_api_without_trusted_hosts`
- `test_validate_runtime_settings_rejects_malformed_production_trusted_hosts`
- `test_runtime_api_trusted_hosts_rejects_unlisted_host`
- `test_runtime_api_trusted_hosts_allows_listed_host`
- `test_sprint_1057_documents_runtime_trusted_host_enforcement`

## Residual Risk

Trusted host enforcement validates inbound Host headers at the application layer. Production
deployments still need customer-approved edge controls for TLS termination, request-size limits,
IP reputation, WAF policy, and distributed rate limiting.
