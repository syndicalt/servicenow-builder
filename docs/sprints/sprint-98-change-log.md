# Sprint 98 Change Log

## Goal

Handle human UAT rejection and story reset signals from ServiceNow without creating accidental rebuild loops.

## Changes

- Added `Ready for Testing` to `Ready` lifecycle planning as `rework_requested`.
- Added `Ready for Testing` to `Draft` lifecycle planning as `story_rejected`.
- Kept `Ready for Testing` to `Work in Progress` unsupported to avoid confusing human takeover with automation ownership.
- Changed the lifecycle webhook API so rework and rejection events:
  - record the lifecycle event,
  - do not enqueue a fulfillment job,
  - write an audit event against the latest related fulfillment job when one exists.
- Added PostgreSQL operational-store support for:
  - recording `rework_requested` without reopening or mutating the latest job,
  - marking the latest job `rejected` when the story returns to Draft.
- Preserved artifact records on story rejection. Artifacts leave the active workstream through job status and audit events, not physical deletion.
- Extended the lifecycle Business Rule generator so reviewed ServiceNow bootstrap specs emit Ready for Testing transitions to:
  - `Complete`,
  - `Ready`,
  - `Draft`.

## Tests

- Added lifecycle planning coverage for UAT rework and story rejection.
- Added FastAPI lifecycle webhook coverage proving neither path enqueues a build.
- Added operational-store coverage proving rework writes an audit event and story rejection marks the latest job rejected without deleting artifacts.
- Updated runtime protocol test doubles for the new lifecycle store methods.
- Updated Business Rule generation coverage for the Ready for Testing return paths.

## Decision

`Ready for Testing -> Ready` is the supported UAT rejection signal for a valid story that needs rework. `Ready for Testing -> Draft` means the story itself was rejected or reset; prior artifacts are preserved for traceability but marked out of the active workstream by rejecting the latest fulfillment job. A rebuild still requires a later approved `Draft -> Ready` lifecycle event.
