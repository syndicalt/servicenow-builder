# Sprint 17 Change Log

## Dry-Run Writeback CLI

- Added `plan-writeback` as an operator-controlled dry-run command.
- The command fetches a story by number, discovers the instance `Ready for Testing` state value, and plans the external build writeback.
- The command prints a safe summary without sys_ids, OAuth secrets, or sensitive story content.
- The command performs no ServiceNow mutation.

## Controls

- Kept state transition planning policy-gated.
- Required explicit `--from-state` so the operator declares the lifecycle state being advanced.
- Preserved the external build boundary: the command plans writeback after build completion, not the build itself.
