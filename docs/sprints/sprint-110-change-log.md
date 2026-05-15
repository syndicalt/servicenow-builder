# Sprint 110 Change Log

## Goal

Add narrow public API abuse controls for the hosted MVP without pretending that in-process limits are a complete Federal production control.

## Changes

- Added `InMemoryRateLimiter` as a small per-process fixed-window rate limiter.
- Added lifecycle webhook request body size enforcement.
- Added lifecycle webhook rate limiting before authentication, validation, or store writes.
- Added admin JSON endpoint rate limiting.
- Verified admin list endpoints cap excessive `limit` values at 100 rows.
- Added runtime environment settings for lifecycle body size, lifecycle rate limits, and admin rate limits.
- Documented `413` oversized-payload behavior and `429` rate-limit behavior.

## Runtime Settings

- `JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES`
- `JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS`
- `JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS`
- `JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS`
- `JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS`

## Tests

- Added lifecycle tests for oversized payload rejection before recording.
- Added lifecycle tests for repeated request bursts returning `429`.
- Added admin endpoint tests for bounded list limits.
- Added admin endpoint tests for runtime-backed rate limiting.
- Added documentation tests for operator guidance and this sprint log.

## Decision

The limiter is intentionally per-process. It is enough to bound the current Railway/PDI MVP process, but production still needs customer-approved edge, WAF, or API gateway controls for distributed rate limiting, request size enforcement, abuse detection, and alerting.
