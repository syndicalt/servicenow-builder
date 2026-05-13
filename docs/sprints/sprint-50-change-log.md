# Sprint 50 Change Log

## Reviewed Delivery Job Writer

- Added `review-delivery-artifact` to create the reviewed handoff job for a real delivery artifact.
- Recorded `reviewer_id`, `artifact_sha256`, `approved_for_delivery=true`, and `delivery_contract=reviewed_export` in the generated job.
- Limited reviewed delivery jobs to delivery artifact kinds that can become ServiceNow attachments.
- Blocked smoke placeholder XML from being promoted into a reviewed export.
- Wrote reviewed delivery job files with write-once artifact semantics so repeated run ids cannot overwrite review evidence.
- Documented the operator path from reviewed delivery job to `plan-artifact-handoff`.
