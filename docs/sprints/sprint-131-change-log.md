# Sprint 131 Change Log

## Flow Snapshot Update Strategy

Sprint 131 added validation-only Flow snapshot update strategy metadata for the Flow Designer path.

## Changes

- Added `flow_snapshot_update_strategy`.
- Added `flow-snapshot-update-strategy-v1`.
- Required retrieved `latest_snapshot` evidence from `sys_hub_flow`.
- Rejected missing and unstable snapshot references.
- Rejected snapshot/version table mutation because snapshot table mutation is not supported in the current Flow path.
- Added `snapshot_update_strategy_version` to Flow builder preflight output.
- Updated ADR 0011, the operator guide, and the production hardening backlog.

## Boundary

There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer. This sprint only defines snapshot evidence rules before future builder work touches Flow snapshot references.

## Verification

- Added positive strategy coverage for retrieved `latest_snapshot` evidence.
- Added negative strategy coverage for missing snapshot evidence.
- Added negative strategy coverage for unstable snapshot references.
- Added negative strategy coverage for snapshot table mutation.
- Added documentation coverage for the Sprint 131 boundary.
