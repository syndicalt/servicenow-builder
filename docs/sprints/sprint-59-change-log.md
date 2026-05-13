# Sprint 59 Change Log

## Lifecycle Event Contract

- Added `LifecycleStateChangeEvent` as the strict inbound contract for ServiceNow lifecycle events.
- Added `plan_story_ready_lifecycle_event()` so `Draft to Ready` on `rm_story` plans sidecar evaluation.
- Set `Work in Progress` as the planned claim state for eligible automated fulfillment, but this sprint performs no ServiceNow mutation.
- Rejected unknown event fields, including ServiceNow internal identifiers such as `story_sys_id`.
- Documented that the ServiceNow bootstrap path should include a Business Rule or equivalent Flow plus a Scripted REST API or outbound REST Message integration.
- Kept the sprint scoped to event parsing and local planning; ServiceNow script creation, webhook authentication, and state-write apply behavior remain explicit follow-on sprints.

## External Build Result CLI

- Added `process-external-build-result` to convert an `ExternalBuildPipelineResult` file into downstream writeback and reviewed delivery job files.
- Successful builds produce one writeback job plus reviewed delivery jobs for Update Set XML and test evidence.
- Failed builds produce only writeback jobs so orchestration can record failure evidence without creating delivery approvals.
- The command is local-only and performs no ServiceNow mutation.

## Verification

- Added lifecycle event unit tests for the `Draft to Ready` trigger, non-triggering transitions, required idempotency/source fields, and unknown-field rejection.
- Added CLI tests for successful and failed external build result processing.
- Updated operator and sidecar architecture docs for the event-driven workflow.
