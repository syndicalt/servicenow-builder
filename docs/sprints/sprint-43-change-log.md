# Sprint 43 Change Log

## Handoff Report

- Added `plan-artifact-handoff` to write a reviewable handoff report for one story.
- Added report generation over artifact jobs with `artifact_kind`, `artifact_path`, and `approved_for_delivery`.
- Report decisions include `attach_to_servicenow`, `write_story_link`, `required_before_ready_for_testing`, exposure, rationale, and optional attachment label.

## Product Boundary

- The handoff report is write-once JSON evidence.
- The command does not attach files to ServiceNow.
- `delivery_evidence` artifacts can be attached only after the policy marks them attachable.
