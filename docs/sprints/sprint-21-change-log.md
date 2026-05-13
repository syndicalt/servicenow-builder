# Sprint 21 Change Log

## Writeback Orchestration Boundary

- Added `execute_writeback()` as the reusable orchestration boundary for automated writeback.
- Added typed request/result models for writeback execution.
- Supported service actor execution without relying on CLI parsing as the integration contract.
- Preserved human actor support for manual operations.

## CLI Adapter

- Refactored `plan-writeback` into a CLI adapter over the orchestration boundary.
- Preserved dry-run behavior, confirmed apply, state discovery, dictionary field validation, and writeback audit artifact creation.
- Kept ServiceNow mutation behind the same policy and audit checks used by automated orchestration.
