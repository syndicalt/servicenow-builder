# Sprint 77 Change Log

## Goal

Make queued fulfillment safer for unattended runtime operation and establish the first ChatGPT implementation-generation adapter without weakening deterministic gates.

## Changes

- Added `run_loop` to the runtime worker so hosts can process queued fulfillment jobs repeatedly instead of relying only on a one-shot worker entrypoint.
- Added a `failure_notifier` callback to `process_one_fulfillment_job()` so handler failures can write human-readable failure evidence back to the ServiceNow story work notes.
- Wired runtime failures to ServiceNow with an `Automated fulfillment failed` work note that includes the lifecycle event id, fulfillment job id, and failure message.
- Redacted runtime secrets from handler failure messages before writing ServiceNow work notes or durable job failure state.
- Preserved durable failure recording even when ServiceNow failure writeback fails; the worker stores the original error plus the notifier error in `last_error`.
- Added `OpenAIResponsesProvider` as the ChatGPT/OpenAI adapter boundary for implementation candidate generation.
- Required model-facing ServiceNow field changes to use explicit `name/value pairs` rather than arbitrary JSON objects, then normalized those pairs back into the internal implementation packet format.

## Verification

- Added focused runtime worker loop tests for completed, idle, and failed queued jobs.
- Added fulfillment worker tests for failure note callbacks and notifier failure isolation.
- Added runtime wiring coverage proving a failed job writes a ServiceNow work note.
- Added OpenAI provider tests for strict structured-output requests, output parsing, API failures, invalid JSON, and rejection of arbitrary field objects.

## Architecture Notes

The webhook remains non-blocking: ServiceNow lifecycle events enqueue work, and worker processing owns fulfillment. Failures must now be visible both in PostgreSQL operational state and on the originating ServiceNow story, because the story remains the user-facing work surface.

The OpenAI adapter is intentionally a boundary, not a bypass. Deterministic eligibility, risk, allowlist, implementation packet, and writeback gates remain authoritative before any model-generated candidate can be accepted.

Sprint 77 does not change the PDI-only `no_authentication` webhook bootstrap posture. Authenticated inbound webhook protection remains required before non-PDI use.
