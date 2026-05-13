# Sprint 20 Change Log

## Writeback Audit Artifact

- Added a writeback audit artifact model for confirmed ServiceNow writeback.
- Required `--actor-id` and `--audit-root` before `plan-writeback --apply` can mutate ServiceNow.
- Supported service principal actor identity for automated orchestration.
- Wrote writeback audit artifacts as write-once JSON files.
- Excluded ServiceNow story sys_id from the audit payload.

## Apply Evidence

- Captured story number, build reference, actor type, actor id, optional execution id, apply intent, applied status, allow decision, planned fields, and validation reasons.
- Preserved dry-run behavior for planning-only usage.
- Kept confirmation mismatch and missing-audit metadata as mutation blockers.
