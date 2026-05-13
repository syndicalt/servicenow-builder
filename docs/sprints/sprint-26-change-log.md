# Sprint 26 Change Log

## Batch Report Artifact

- Added sanitized batch report generation for writeback orchestration.
- Added write-once JSON artifact support for generic run-level evidence.
- Wired `run-writeback-batch` to write a batch report artifact.
- Excluded ServiceNow sys_ids from the batch report.

## Report Contents

- Execution id.
- Actor id.
- Capability result.
- Summary counts.
- Per-story outcome records.

## Safety Boundary

- Kept per-story audit artifacts separate from batch report artifacts.
- Preserved write-once artifact behavior.
- Documented that batch reports contain no ServiceNow sys_ids.
