# Sprint 25 Change Log

## Writeback Job File Ingestion

- Added typed job records for external build-result writeback jobs.
- Added JSON writeback job file loading.
- Defaulted job confirmation to the story number for service actor orchestration.
- Rejected an empty job file.

## CLI Adapter

- Added `run-writeback-batch`.
- Mapped job files to typed writeback execution requests.
- Reused batch orchestration, capability preflight, idempotency, actor identity, and audit artifact behavior.

## Safety Boundary

- Avoided ad hoc dict handoff between external build and writeback orchestration.
- Kept apply explicit with `--apply`.
- Required actor identity and audit root for batch execution.
