# Sprint 48 Change Log

## Delivery Attachment Audit

- Added write-once attachment audit support for `attach-delivery-artifacts --apply`.
- Required `--audit-root` and `--run-id` for apply runs so automated delivery attachment writes leave a durable local record.
- Blocked apply before any ServiceNow attachment call when the requested attachment audit artifact already exists.
- Captured delivery artifact kind, artifact path, attachment label, and ServiceNow attachment sys_ids returned by the Attachment API.
- Kept the audit record scoped to story number and delivery attachment results; it does not store the ServiceNow `story_sys_id`.
- Left dry-run behavior unchanged so attachment planning can still be reviewed without ServiceNow mutation.
