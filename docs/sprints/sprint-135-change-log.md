# Sprint 135 Change Log

## Flow Unsupported Reason Codes

Sprint 135 added machine-readable unsupported reason codes to the Flow Designer preflight path.
This is the Flow unsupported reason codes sprint.

## Changes

- Added `unsupported_reason_codes` to `flow-builder-readiness-v1`.
- Added `unsupported_reason_codes` to Flow builder preflight output.
- Added `flow_builder_not_implemented`.
- Added `runtime_generation_disabled`.
- Added `retrieved_update_set_handoff_disabled`.
- Updated ADR 0011, the operator guide, and the production hardening backlog.

## Boundary

There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer. This sprint only makes unsupported Flow work easier to route without parsing human-readable text.

## Verification

- Added readiness contract coverage for unsupported reason codes.
- Added builder plan coverage for unsupported reason codes.
- Added documentation coverage for the Sprint 135 boundary.
