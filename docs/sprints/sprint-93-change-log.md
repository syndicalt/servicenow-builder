# Sprint 93 Change Log

## Goal

Replace table-specific automation gating with capability-based suitability and add generic dictionary field creation plus form placement as the baseline capability.

## Changes

- Added capability assessment models and target-agnostic deterministic analysis.
- Added instance discovery context before model calls so implementation packets include target table metadata, dictionary fields, form sections, form elements, and ACL indicators.
- Classified `STRY0010001` as automatable dictionary/form work for `incident.u_antics`.
- Preserved `STRY0010013` as automatable dictionary/form work for `rm_story.u_ai_review_notes`.
- Generalized dictionary, documentation, and form layout customer update generation beyond `rm_story`.
- Kept retrieved Update Set handoff as the ServiceNow-native review surface.
- Wrote `Needs Clarification` feedback when a story is missing details needed for automated fulfillment.

## Tests

- Added analyzer coverage for automated, needs-clarification, unsupported-capability, and manual-developer-build outcomes.
- Added discovery-backed implementation packet coverage.
- Added generic dictionary/form builder coverage for Incident form placement below Description.
- Added runtime coverage for the Incident UAT path.

## Decision

The gate now evaluates whether the pipeline supports the requested capability and whether the story is clear and low-complexity enough. Table names affect risk and metadata lookup, not baseline eligibility.
