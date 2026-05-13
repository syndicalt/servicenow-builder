# Sprint 65 Change Log

## Lifecycle ServiceNow Record Plan

- Added `lifecycle_webhook_servicenow_record_plan()` to derive explicit ServiceNow records from the reviewed lifecycle webhook bootstrap bundle.
- Added `servicenow_records` to the `plan-lifecycle-business-rule` artifact.
- Planned `sys_rest_message`, `sys_rest_message_fn`, and `sys_script` records with `insert_or_update` operations.
- Included lookup keys and write fields for each ServiceNow table so future apply code does not infer record shape from script text.
- Kept this sprint to planning only with no live ServiceNow apply.

## Verification

- Added bootstrap tests for the generated ServiceNow record plan.
- Updated CLI tests to require `servicenow_records` in the local artifact.
- Updated operator documentation to describe the record plan and live-apply boundary.
