# Sprint 22 Change Log

## Writeback Idempotency

- Added idempotency handling for automated writeback retries.
- Used the writeback audit artifact as the idempotency record.
- Returned a no-op result when a retry finds an existing story/build audit artifact.
- Prevented a retry from issuing another ServiceNow update after the first successful apply.
- Added remote writeback idempotency using target story state plus matching `u_ai_build_reference`.
- Requested writeback idempotency fields from ServiceNow story reads.

## Orchestration Semantics

- Preserved write-once audit artifacts.
- Kept dry-run behavior unchanged.
- Exposed `idempotent`, `writeback_already_recorded`, and `remote_writeback_already_applied` in the orchestration result for callers.
