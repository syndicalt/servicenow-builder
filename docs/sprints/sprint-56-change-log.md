# Sprint 56 Change Log

## Reviewed Delivery Lifecycle Manifest

- Extended `run-reviewed-delivery-smoke` to write a reviewed delivery lifecycle manifest.
- Stored the manifest under `reviewed-delivery-lifecycle-manifests`.
- Referenced the delivery artifact, `reviewed_delivery_job`, and `artifact_handoff_report` by path and SHA-256.
- Recorded the dry-run `delivery_attachment_plan` with planned and applied counts.
- Kept the manifest free of ServiceNow `sys_id` values.
