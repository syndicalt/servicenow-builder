# Sprint 19 Change Log

## Confirmed Apply Gate

- Added confirmed apply support to `plan-writeback`.
- Preserved dry-run default behavior unless `--apply` is passed.
- Required `--confirm-story-number` to match the fetched story before mutation.
- Applied only the validated structured fields plus work notes.

## Safety Boundary

- Reused state discovery, dictionary field discovery, and policy validation before any update.
- Blocked mutation on confirmation mismatch.
- Kept story sys_ids and OAuth secrets out of user-facing output.
