# Sprint 97 Change Log

## Goal

Close the ServiceNow user-facing lifecycle loop after UAT without triggering another automated build.

## Changes

- Added `Ready for Testing` to `Complete` lifecycle planning as `close_story`.
- Kept `Draft` to `Ready` as the only lifecycle transition that enqueues automated fulfillment.
- Changed the lifecycle webhook API so Complete events:
  - record the lifecycle event,
  - do not enqueue a fulfillment job,
  - write a `story_completed` audit event against the latest related fulfillment job when one exists.
- Added PostgreSQL operational-store support for closing the latest fulfillment job for a story after ServiceNow marks the story Complete.
- Extended the lifecycle Business Rule generator so reviewed ServiceNow bootstrap specs can emit both:
  - `Draft` to `Ready`,
  - `Ready for Testing` to `Complete`.
- Added CLI flags for the Complete closeout transition:
  - `--ready-for-testing-state-value`
  - `--complete-state-value`

## Tests

- Added lifecycle planning coverage for `Ready for Testing` to `Complete`.
- Added FastAPI lifecycle webhook coverage proving Complete closeout does not enqueue a build.
- Added operational-store coverage proving the closeout path writes a `story_completed` job event.
- Added bootstrap and CLI coverage for reviewed Business Rule generation with both lifecycle transitions.

## Decision

The Complete transition is a closeout signal, not a build signal. Human preview, commit, and UAT remain inside ServiceNow. When the story reaches Complete, the sidecar records the closeout for traceability and closes any remaining operational loop without generating new candidates or mutating ServiceNow again.
