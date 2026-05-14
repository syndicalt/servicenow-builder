# ADR 0005: Admin Authentication Strategy

## Status

Accepted.

## Context

Sprint 101 added a read-only `/admin` console with local Basic authentication for the PDI/Railway MVP. That is useful for development, but it is not a production identity model.

The original Sprint 102 backlog item proposed ServiceNow role-backed admin authentication. That wording is too strong because many customer ServiceNow instances use SSO. In those environments, the sidecar should not assume it can inspect, reuse, or trust a ServiceNow browser session cookie. ServiceNow UI session behavior, IdP redirects, cookie scope, and customer SSO policy are outside the sidecar's control.

## Decision

Introduce an explicit admin auth strategy boundary:

- `disabled`: default. `/admin` fails closed.
- `dev_basic`: development-only Basic auth using local env vars.
- `oidc`: reserved for customer IdP OIDC integration.
- `servicenow_oauth`: reserved for ServiceNow OAuth authorization code integration.

ServiceNow role-backed browser authentication is not assumed for production. The preferred production path is customer IdP OIDC, where the sidecar validates tokens from the same identity provider used by ServiceNow and authorizes access from customer-approved group or role claims. ServiceNow OAuth authorization code remains a possible production path only when the customer approves a ServiceNow OAuth app, redirect URI, scopes, and role-check API access.

## Consequences

- Basic auth cannot be accidentally enabled by setting only username and password.
- `dev_basic` is blocked outside `JEDI_ENVIRONMENT=development`.
- `oidc` and `servicenow_oauth` fail closed until implemented.
- A future production implementation must define token validation, session handling, logout behavior, role/group mapping, callback URLs, secret rotation, and failure behavior before enabling browser access.
