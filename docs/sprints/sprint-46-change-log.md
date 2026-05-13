# Sprint 46 Change Log

## Delivery Attachment Gate

- Added `attach-delivery-artifacts` as the controlled attachment path for approved delivery evidence.
- Added ServiceNow Attachment API support for `rm_story` files.
- Kept attachment application dry-run by default.
- Required `--apply`, `--confirm-story-number`, and `--actor-id` before uploading files.

## Product Boundary

- Only handoff decisions with `attach_to_servicenow=true` are eligible.
- Approved Update Set XML and Test Evidence Bundle are the intended delivery artifact classes.
- Internal audit evidence remains link-only and is not attached.
- Attachment upload does not change story state or structured AI fields.
