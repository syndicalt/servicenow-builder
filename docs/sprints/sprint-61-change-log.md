# Sprint 61 Change Log

## Build Claim Writeback Planner

- Added `plan_story_build_claim_writeback()` to plan the story claim before external build handoff.
- Allowed `Ready to Work in Progress` only when state transitions are enabled and explicitly allowlisted.
- Planned `u_ai_status=Build In Progress` with optional `u_ai_candidate_artifact` reference.
- Included the lifecycle event id in work notes so the claim can be traced to the ServiceNow event that started orchestration.
- Failed closed with `State transitions are disabled` or a not-allowlisted transition reason without writing a `state` field.
- Kept this sprint scoped to planning, not live apply.

## Verification

- Added writeback tests for allowed `Ready` to `Work in Progress` claim planning.
- Added writeback tests proving non-allowlisted current states cannot be claimed.
- Updated operator documentation for the build claim writeback boundary.
