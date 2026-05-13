# Sprint 63 Change Log

## Lifecycle Business Rule Bootstrap

- Chose Business Rule first for the `rm_story` lifecycle emitter because it is deterministic, table-local, and reviewable as a ServiceNow script artifact.
- Deferred Flow to later approval orchestration work instead of using it as the low-level state-change trigger.
- Added `build_lifecycle_business_rule_spec()` to generate an after-update `rm_story` Business Rule spec for `Draft to Ready`.
- Added `plan-lifecycle-business-rule` to write the reviewable spec as a write-once local artifact.
- Generated payloads emit `story_state_changed` with story number, event id, correlation id, source, timestamp, and integration identity.
- Prevented `story_sys_id` from crossing the lifecycle event boundary.
- Required HTTPS endpoints for the sidecar lifecycle receiver.

## Verification

- Added bootstrap tests for the generated Business Rule condition and script.
- Added CLI tests for writing the Business Rule spec artifact.
- Updated operator documentation with the Business Rule first decision and the reviewed bootstrap command.
