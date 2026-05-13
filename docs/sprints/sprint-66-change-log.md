# Sprint 66 Change Log

## Lifecycle Webhook Apply

- Added generic `upsert_table_record()` support to the ServiceNow client.
- Added `apply_lifecycle_webhook_records()` to apply the reviewed lifecycle webhook record plan.
- Added `apply-lifecycle-webhook` CLI with explicit `--confirm-table rm_story` and `--confirm-records` controls.
- Applied planned `sys_rest_message`, `sys_rest_message_fn`, and `sys_script` records through `insert_or_update` semantics.
- Wrote lifecycle webhook audit output after successful apply.
- Failed closed with `lifecycle_webhook_confirmation_required` when confirmation is missing.

## Verification

- Added ServiceNow client tests for create-vs-update upsert behavior.
- Added bootstrap tests for confirmation and planned-record application.
- Added CLI tests for confirmation failure and successful audited apply.
- Updated operator documentation for the live apply command and audit requirement.
