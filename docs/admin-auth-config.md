# Admin Auth Configuration

`JEDI_ADMIN_AUTH_MODE` controls browser access to the HTML admin console (`GET /admin` and
`GET /admin/artifacts/{artifact_id}`). The JSON admin and artifact APIs are a separate boundary:
they always require `Authorization: Bearer <JEDI_ADMIN_API_TOKEN>`, regardless of the console
mode.

## Runtime Modes

| Mode | Status | Behavior |
|---|---|---|
| `disabled` | Implemented, default | Browser console returns `503 admin console authentication is disabled`. JSON admin APIs remain available with the bearer token. This is the supported interim production posture. |
| `dev_basic` | Implemented | HTTP Basic auth for the browser console, development only. Startup validation rejects `dev_basic` when `JEDI_ENVIRONMENT=production`, and request handling returns `503 dev_basic admin auth is development-only` for any non-development environment. |
| `oidc` | Reserved | Future customer IdP OIDC integration. Requests return `501 admin auth mode is not implemented: oidc`; production startup rejects the mode. |
| `servicenow_oauth` | Reserved | Future ServiceNow OAuth authorization code integration. Requests return `501 admin auth mode is not implemented: servicenow_oauth`; production startup rejects the mode. |

Any other mode value is rejected at settings load, at production startup validation, and at
request time (`503 admin auth mode is not supported`). Mode strings are never normalized into a
match: padded, mixed-case, or whitespace-bearing values fail closed.

## Production Posture: Console Disabled, Bearer-Protected JSON APIs

Production runs with the browser console disabled while retaining authenticated operator
diagnostics:

```text
JEDI_ENVIRONMENT=production
JEDI_RUNTIME_ROLE=api
JEDI_ADMIN_AUTH_MODE=disabled
JEDI_ADMIN_API_TOKEN=<strong random token, at least 32 characters>
```

In this posture:

- `GET /admin` and `GET /admin/artifacts/{artifact_id}` return `503` because browser admin auth
  is disabled.
- The JSON endpoints require `Authorization: Bearer <JEDI_ADMIN_API_TOKEN>`:
  - `GET /admin/jobs`
  - `GET /admin/lifecycle-events`
  - `GET /admin/alerts`
  - `GET /admin/operations`
  - `GET /artifacts/{artifact_id}`
  - `GET /jobs/{job_id}/artifacts`
  - `GET /jobs/{job_id}/events`

Token rules, enforced at production startup and again at request time:

- Minimum 32 characters, maximum 8192 bytes, ASCII only, no leading/trailing padding, no
  whitespace or control characters.
- Missing configured token: admin APIs return `503 admin artifact API is not configured`.
- Malformed configured token: admin APIs return `503 admin artifact API token is invalid`.
- Missing or non-Bearer `Authorization` header: `401 admin bearer token required`.
- Malformed or incorrect presented token: `403 admin bearer token rejected`.
- Comparison uses `secrets.compare_digest`; the error does not distinguish a malformed token from
  a wrong one beyond the fixed diagnostics above.

Public production roles also reject configured `JEDI_ADMIN_CONSOLE_USERNAME` and
`JEDI_ADMIN_CONSOLE_PASSWORD` at startup: Basic-auth credentials are development-only and must
not be deployed beside the bearer-only production posture.

All admin endpoints share the admin rate limiter (default 120 requests per 60 seconds per
process) and return `429` with `Retry-After` when exceeded. Diagnostic JSON routes send
`Cache-Control: no-store` and `Vary: Authorization`; HTML console routes add a restrictive
Content-Security-Policy, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, and a
`Permissions-Policy` denylist.

## Development Posture: `dev_basic`

```text
JEDI_ENVIRONMENT=development
JEDI_ADMIN_AUTH_MODE=dev_basic
JEDI_ADMIN_CONSOLE_USERNAME=<operator username>
JEDI_ADMIN_CONSOLE_PASSWORD=<strong password>
```

- Missing username or password configuration: `503 admin console is not configured`.
- Malformed configured credentials (non-ASCII, padded, whitespace/control characters, over
  8192 bytes): `503 admin console credentials are invalid`.
- Missing, undecodable, or malformed Basic credentials: `401 admin console credentials required`
  with `WWW-Authenticate: Basic realm="jedi-admin"`.
- Username and password are compared with `secrets.compare_digest`.

Do not use `dev_basic` for production. Basic auth has no MFA, no per-user identity, and no
session expiry; it exists for PDI/Railway MVP testing only.

## OIDC Configuration (Reserved)

Recommended production path once implemented: authenticate the sidecar directly with the customer
identity provider using OIDC. This is SSO-compatible without depending on a ServiceNow UI session.

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
6. Runtime validates issuer, audience, signature, nonce, expiration, and required group or role
   claims.
7. Runtime creates a server-side admin session.

Do not rely on a ServiceNow browser session cookie for OIDC mode. The sidecar should trust the
customer IdP token validation result, not ServiceNow UI cookie state.

## ServiceNow OAuth Configuration (Reserved)

Alternative production path once implemented: ServiceNow OAuth authorization code grant.

This mode is only appropriate when the customer approves ServiceNow as the OAuth authorization
server for sidecar admin access and grants a way to verify user authorization after login.
ServiceNow SSO can still be involved because ServiceNow may redirect users to the configured IdP
during the authorization code grant.

Required future ServiceNow setup:

- Create an inbound OAuth application registry record for the sidecar.
- Use authorization code grant.
- Register redirect URI: `https://<sidecar-host>/admin/auth/servicenow/callback`.
- Define approved scopes for the minimum API access needed.
- Confirm whether consent is required.
- Ensure the authenticated user can call the role-check or identity endpoint selected for
  authorization.
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

Do not rely on a ServiceNow browser session cookie in this mode either. The sidecar must validate
the OAuth callback and perform an explicit authorization check.

## Current Implementation Boundary

OIDC and ServiceNow OAuth are reserved but not implemented. The runtime provides the strategy
switch, restricts Basic auth to development, enforces the bearer-token JSON boundary, and records
the concrete configuration requirements above so a future implementation sprint can adopt the
customer-approved production path. Until then, the only supported production posture is
`JEDI_ADMIN_AUTH_MODE=disabled` with a strong `JEDI_ADMIN_API_TOKEN`.

Related controls: lifecycle webhook authentication is documented in `docs/operator-guide.md`
under "Lifecycle Webhook Authentication"; the full production startup checklist is under
"Production Runtime Fail-Closed Checklist" in the same file.
