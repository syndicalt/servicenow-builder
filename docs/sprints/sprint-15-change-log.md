# Sprint 15 Change Log

## Writeback Boundary

- Added a policy-gated writeback planner for external build result handling.
- Modeled successful, failed, and blocked external build result outcomes.
- Planned `Ready for Testing` state advancement only after a successful external build result and an allowlisted state transition.
- Routed failed external build results to human review without changing story state.

## ServiceNow Integration

- Added a low-level ServiceNow Table API PATCH primitive for story field updates.
- Kept mutation out of the pipeline orchestration path until lifecycle policy, state mapping, and operator controls are explicitly wired.
- Preserved secret redaction for write requests.

## Test Evidence

- Added tests for successful build writeback planning, disabled transitions, and failed-build human-review routing.
- Added tests proving the PATCH primitive sends JSON to `rm_story` without exposing OAuth secrets.
