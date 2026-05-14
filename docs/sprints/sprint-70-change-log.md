# Sprint 70 Change Log

## Goal

Add the non-blocking Lifecycle Webhook API boundary for ServiceNow lifecycle events.

## Changes

- Added `jedi_devproject.lifecycle_api` with `create_lifecycle_api()`.
- Added `POST /lifecycle/events` to validate `LifecycleStateChangeEvent` payloads through FastAPI and Pydantic.
- Returned `202 Accepted` for valid lifecycle events after recording operational state.
- Enqueued fulfillment only for the supported `rm_story` `Draft` to `Ready` transition.
- Kept unsupported transitions recorded but not enqueued.
- Added `GET /health` for runtime health checks.
- Added `fastapi` and `uvicorn` as runtime dependencies.

## Verification

- Added webhook API tests for ready-event enqueueing, unsupported transition handling, forbidden `story_sys_id` rejection, and health checks.
- Added operator guide documentation for the API contract and `DATABASE_URL` runtime wiring.

## Architecture Notes

The webhook path is non-blocking. It validates, records, enqueues, and returns. Fulfillment work must run in a worker process that claims jobs from PostgreSQL; it must not run inside the ServiceNow webhook request.
