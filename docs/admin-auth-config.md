# Admin Auth Configuration

## Current Runtime Modes

`JEDI_ADMIN_AUTH_MODE` controls browser access to `/admin` and `/admin/artifacts/{artifact_id}`.

| Mode | Status | Use |
|---|---|---|
| `disabled` | Implemented | Default fail-closed browser mode. Browser admin console is unavailable; production API deployments must configure `JEDI_ADMIN_API_TOKEN` for bearer-protected JSON diagnostics. |
| `dev_basic` | Implemented | Development-only Basic auth for PDI/Railway MVP testing. |
| `oidc` | Reserved | Future customer IdP OIDC integration. Fails closed today. |
| `servicenow_oauth` | Reserved | Future ServiceNow OAuth authorization code integration. Fails closed today. |

Production can run with the browser admin console disabled while retaining authenticated operator
diagnostics through the JSON admin and artifact APIs:

```text
JEDI_ENVIRONMENT=production
JEDI_RUNTIME_ROLE=api
JEDI_ADMIN_AUTH_MODE=disabled
JEDI_ADMIN_API_TOKEN=<strong random token, at least 32 characters>
```

In this posture, `/admin` and `/admin/artifacts/{artifact_id}` return `503` because browser admin
auth is disabled. JSON admin endpoints such as `/admin/jobs`, `/jobs/{job_id}/events`, and artifact
APIs require `Authorization: Bearer <JEDI_ADMIN_API_TOKEN>`.

`dev_basic` requires:

```text
JEDI_ENVIRONMENT=development
JEDI_ADMIN_AUTH_MODE=dev_basic
JEDI_ADMIN_CONSOLE_USERNAME=<operator username>
JEDI_ADMIN_CONSOLE_PASSWORD=<strong password>
```

Do not use `dev_basic` for production. The runtime rejects `dev_basic` when `JEDI_ENVIRONMENT` is anything other than `development`.

## OIDC Configuration

Recommended production path: authenticate the sidecar directly with the customer identity provider using OIDC. This is SSO-compatible without depending on a ServiceNow UI session.

Required future configuration:

```text
JEDI_ENVIRONMENT=production
JEDI_ADMIN_AUTH_MODE=oidc
JEDI_ADMIN_OIDC_ISSUER=https://<customer-idp>/<tenant>/v2.0
JEDI_ADMIN_OIDC_CLIENT_ID=<sidecar client id>
JEDI_ADMIN_OIDC_CLIENT_SECRET=<sidecar client secret>
JEDI_ADMIN_OIDC_REDIRECT_URI=https://<sidecar-host>/admin/auth/callback
JEDI_ADMIN_OIDC_ALLOWED_GROUPS=<group id or claim value list>
JEDI_ADMIN_OIDC_ALLOWED_ROLES=<role claim value list>
JEDI_ADMIN_OIDC_SCOPES=openid profile email
JEDI_ADMIN_SESSION_SECRET=<server-side session signing secret>
```

Expected production behavior:

1. User opens `/admin`.
2. Runtime redirects to the customer IdP authorization endpoint.
3. IdP authenticates the user through the customer's SSO/MFA policy.
4. Runtime receives an authorization code at `/admin/auth/callback`.
5. Runtime exchanges the code server-side.
6. Runtime validates issuer, audience, signature, nonce, expiration, and required group or role claims.
7. Runtime creates a server-side admin session.

Do not rely on a ServiceNow browser session cookie for OIDC mode. The sidecar should trust the customer IdP token validation result, not ServiceNow UI cookie state.

## ServiceNow OAuth Configuration

Alternative production path: ServiceNow OAuth authorization code grant.

This mode is only appropriate when the customer approves ServiceNow as the OAuth authorization server for sidecar admin access and grants a way to verify user authorization after login. ServiceNow SSO can still be involved because ServiceNow may redirect users to the configured IdP during the authorization code grant.

Required future ServiceNow setup:

- Create an inbound OAuth application registry record for the sidecar.
- Use authorization code grant.
- Register redirect URI: `https://<sidecar-host>/admin/auth/servicenow/callback`.
- Define approved scopes for the minimum API access needed.
- Confirm whether consent is required.
- Ensure the authenticated user can call the role-check or identity endpoint selected for authorization.
- Define the required ServiceNow role, for example `admin` or a customer-owned `x_jedi.admin`.

Required future runtime configuration:

```text
JEDI_ENVIRONMENT=production
JEDI_ADMIN_AUTH_MODE=servicenow_oauth
JEDI_ADMIN_SERVICENOW_AUTHORIZATION_URL=https://<instance>.service-now.com/oauth_auth.do
JEDI_ADMIN_SERVICENOW_TOKEN_URL=https://<instance>.service-now.com/oauth_token.do
JEDI_ADMIN_SERVICENOW_CLIENT_ID=<oauth app client id>
JEDI_ADMIN_SERVICENOW_CLIENT_SECRET=<oauth app client secret>
JEDI_ADMIN_SERVICENOW_REDIRECT_URI=https://<sidecar-host>/admin/auth/servicenow/callback
JEDI_ADMIN_SERVICENOW_REQUIRED_ROLE=x_jedi.admin
JEDI_ADMIN_SESSION_SECRET=<server-side session signing secret>
```

Expected production behavior:

1. User opens `/admin`.
2. Runtime redirects to ServiceNow's OAuth authorization endpoint.
3. ServiceNow authenticates the user, possibly through SSO.
4. Runtime receives an authorization code at the registered callback.
5. Runtime exchanges the code server-side.
6. Runtime calls an approved ServiceNow API to verify the user's required role.
7. Runtime creates a server-side admin session only when the role check passes.

Do not rely on a ServiceNow browser session cookie in this mode either. The sidecar must validate the OAuth callback and perform an explicit authorization check.

## Current Sprint 102 Boundary

Sprint 102 does not implement OIDC or ServiceNow OAuth. It adds the strategy switch, makes Basic auth development-only, and records the concrete configuration requirements so the next implementation sprint can choose the customer-approved production path.
