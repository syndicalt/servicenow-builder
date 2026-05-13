# Sprint 42 Change Log

## Artifact Handoff Contract

- Added an artifact handoff policy that classifies artifacts as internal audit evidence or delivery evidence.
- Kept implementation packet, implementation candidate, lifecycle manifest, and writeback audit artifacts out of ServiceNow attachments by default.
- Marked Approved Update Set XML and Test Evidence Bundle as delivery artifacts that may be attached after approval.

## Product Boundary

- Artifact links remain appropriate for traceability during writeback.
- Attachments are reserved for tester/reviewer-facing delivery evidence.
- Ready for Testing writeback does not imply that internal audit artifacts should be attached to the story.
