# Sprint 73 Change Log

## Goal

Add runtime wiring for API and worker processes from environment configuration.

## Changes

- Added `jedi_devproject.runtime`.
- Added `RuntimeSettings` and `load_runtime_settings()` for required runtime environment values.
- Required `DATABASE_URL`, ServiceNow OAuth settings, worker identity, and audit root.
- Added `create_runtime_api()` to wire the Lifecycle Webhook API to the PostgreSQL operational store.
- Added `process_one_runtime_fulfillment()` to wire the PostgreSQL store, ServiceNow client, and build-claim fulfillment handler.
- Kept store creation and HTTP transport injectable so tests remain offline and production wiring remains explicit.

## Verification

- Added runtime tests for missing settings, valid settings, API store wiring, worker fulfillment wiring, and idle worker behavior.

## Architecture Notes

Runtime wiring now has one shared configuration path for the API and worker. The API accepts and enqueues lifecycle events; the worker claims PostgreSQL jobs and calls the guarded build-claim handler.
