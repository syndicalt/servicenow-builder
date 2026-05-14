# Admin Console Design

## Context

The product work surface remains ServiceNow. The hosted runtime still needs a small operator console for diagnostics, but it must not become a parallel workflow engine or an unsafe mutation surface.

## Decision

Build a read-only admin console inside the existing FastAPI runtime at `/admin`. Use local HTTP Basic authentication for the MVP with credentials supplied by Railway environment variables:

- `JEDI_ADMIN_CONSOLE_USERNAME`
- `JEDI_ADMIN_CONSOLE_PASSWORD`

Keep `JEDI_ADMIN_API_TOKEN` for API clients. Browser operators should not paste or store bearer tokens.

## Scope

The console renders:

- Recent fulfillment jobs.
- Recent lifecycle events.
- Job status, story number, attempt count, lock metadata, and latest error.
- Artifact links for each visible job when artifact references exist.

The console does not include retry, reject, rebuild, preview, commit, or ServiceNow mutation controls. Those actions require separate lifecycle design and authorization review.

## Data Flow

`GET /admin` challenges with Basic auth, validates configured console credentials, reads recent jobs and lifecycle events from the existing runtime store, reads artifact refs for displayed jobs, and returns server-rendered HTML. The page uses sanitized summary records already exposed by the admin API and does not render raw lifecycle payload JSON or ServiceNow sys_ids.

## Security

If console credentials are not configured, `/admin` returns `503`. Missing or invalid Basic credentials return `401` with `WWW-Authenticate: Basic`. Credential comparison uses constant-time comparison. Production ServiceNow/OIDC role-backed authentication is deferred to a dedicated security integration sprint.

## Testing

Tests must cover missing credentials, unauthenticated access, invalid credentials, successful HTML rendering, job/event content, artifact links, and absence of raw lifecycle payload values.
