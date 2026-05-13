# Sprint 45 Change Log

## Handoff Summary Writeback

- Added `write-artifact-handoff-summary` to write a short handoff report summary to ServiceNow `work_notes`.
- Kept the command dry-run by default.
- Required `--apply`, `--confirm-story-number`, and `--actor-id` before mutation.

## Product Boundary

- The command writes only `work_notes`.
- It does not attach files to ServiceNow.
- It does not change story state or structured AI writeback fields.
