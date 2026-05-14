# Sprint 103 Change Log

## Goal

Harden the public lifecycle webhook boundary so non-development runtimes cannot accept unauthenticated ServiceNow lifecycle events.

## Changes

- Added lifecycle webhook auth modes to the FastAPI receiver:
  - `disabled`: development-only.
  - `hmac_sha256`: timestamped request signing with replay-window enforcement.
  - `shared_secret`: interim static-secret mode for simple test emitters.
  - `servicenow_oauth`: reserved and fail-closed until designed.
- Changed `POST /lifecycle/events` to authenticate the raw request body before parsing or recording lifecycle events.
- Wired runtime settings:
  - `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE`
  - `JEDI_LIFECYCLE_WEBHOOK_SECRET`
  - `JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS`
- Added lifecycle webhook secret redaction to runtime failure handling.
- Documented production-shaped HMAC headers, signature base string, replay window behavior, and the development-only disabled mode.

## Tests

- Added FastAPI coverage proving missing signatures, bad signatures, and stale timestamps reject before store mutation.
- Added runtime settings coverage for HMAC webhook config.
- Added production fail-closed coverage when lifecycle webhook auth is disabled outside development.

## Decision

HMAC is the correct next step because it is simple enough for the current ServiceNow emitter but materially stronger than a static shared-secret header. It authenticates the exact raw payload and constrains replay risk with a timestamp window. OAuth remains the likely target for a mature production posture, but it needs a separate design for token validation, issuer trust, and SSO/Federal constraints.
