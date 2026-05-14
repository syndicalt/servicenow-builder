# Sprint 101 Change Log

## Goal

Create the first browser-based admin console without moving the product work surface out of ServiceNow.

## Changes

- Added `/admin` as a read-only HTML console served by the existing FastAPI runtime.
- Added local Basic auth for browser operators with `JEDI_ADMIN_CONSOLE_USERNAME` and `JEDI_ADMIN_CONSOLE_PASSWORD`.
- Kept bearer-token auth for JSON admin API clients.
- Rendered recent fulfillment jobs, recent lifecycle events, latest errors, lock metadata, and artifact links.
- Added `/admin/artifacts/{artifact_id}` so artifact links remain inside the Basic-auth console instead of pointing operators at bearer-token JSON endpoints.
- Escaped dynamic HTML content and kept raw lifecycle payload JSON out of the dashboard.
- Documented console configuration and read-only limitations.

## Verification

- Focused console tests: `6 passed`.
- Full lint, type, and coverage gate before deployment.

## Decision

Use local Basic auth for the MVP because it is simple, auditable, and adequate behind Railway HTTPS for development. ServiceNow role-backed SSO remains the production target, but it should be handled as a separate security integration sprint with explicit OAuth/OIDC session validation and role checks.
