# Sprint 16 Change Log

## Instance State Discovery

- Added ServiceNow `sys_choice` discovery for active `rm_story.state` choices.
- Added a typed story state choice model for label, value, sequence, and inactive status.
- Added instance state mapping for `Ready for Testing` so writeback uses the instance value instead of a hardcoded label.
- Made the mapping fails closed behavior explicit when `Ready for Testing` is not discoverable.

## Writeback Safety

- Preserved the policy-gated writeback planner from Sprint 15.
- Kept live mutation out of pipeline orchestration.
- Required instance state mapping before any automated story state transition can be planned.
