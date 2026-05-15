# Sprint 130 Change Log

## Flow Customer Update Strategy

Sprint 130 added validation-only Flow customer update strategy metadata for the Flow Designer path.

## Changes

- Added `flow_customer_update_strategy`.
- Added `flow-customer-update-strategy-v1`.
- Defined the ServiceNow-style `table_sys_id` customer update naming pattern for approved Flow tables.
- Rejected unsupported Flow tables and unstable non-hex sys_ids.
- Defined rollback strategy coverage for the currently allowed Flow graph diff operations: `add_action` and `update_condition`.
- Added `customer_update_strategy_version` to Flow builder preflight output.
- Updated ADR 0011, the operator guide, and the production hardening backlog.

## Boundary

There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer. This sprint only proves that customer update naming and `rollback_customer_update_strategy_defined` evidence are explicit before future builder work starts.

## Verification

- Added positive strategy coverage for an approved `sys_hub_action_instance` customer update name.
- Added negative strategy coverage for unsupported Flow tables.
- Added negative strategy coverage for unstable sys_ids.
- Added documentation coverage for the Sprint 130 boundary.
