# Sprint 60 Change Log

## Lifecycle Event Processor CLI

- Added `process-lifecycle-event` to validate a lifecycle event JSON file and write a local orchestration plan.
- Wrote lifecycle plans under `lifecycle-event-plans` with write-once artifact semantics.
- Preserved the `Draft to Ready` trigger behavior from `LifecycleStateChangeEvent`.
- Recorded `Work in Progress` as the planned claim state without applying that state to ServiceNow.
- Failed closed with `reason=invalid_lifecycle_event` when an event contains forbidden fields such as `story_sys_id`.
- Kept the command local-only with no ServiceNow mutation and no live webhook listener.

## Verification

- Added CLI tests for valid `Draft to Ready` lifecycle event processing.
- Added CLI tests proving invalid lifecycle events do not create plan artifacts.
- Updated the operator guide with the event processor command and expected output path.
