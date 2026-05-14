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
- Changed form layout generation to emit the captured ServiceNow `sys_ui_section` record-update shape for form placement instead of synthetic form XML.
- Constrained OpenAI structured output so model-produced change `sys_id` values must be `null`; provider validation still rejects any non-null `sys_id`.

## Tests

- Added analyzer coverage for automated, needs-clarification, unsupported-capability, and manual-developer-build outcomes.
- Added discovery-backed implementation packet coverage.
- Added generic dictionary/form builder coverage for Incident form placement below Description.
- Added runtime coverage for the Incident UAT path.
- Verified `STRY0010001` live after deployment on May 14, 2026:
  - Story sys_id `ad8154aec3b0c710913fbf12b4013126` moved to `state=-7` and `u_ai_status=Ready for Testing`.
  - Retrieved Update Set `JEDI STRY0010001 - AI Candidate` was created as `ce910dfb81bb2295f25a60f73c1dfae3` in `loaded` state.
  - The retrieved Update Set contained three customer updates: `sys_dictionary_incident_u_antics`, `sys_documentation_incident_u_antics_en`, and `sys_ui_section_bf1d96e3c0a801640190725e63f8ac80`.
  - The Incident form element `u_antics` exists in section `bf1d96e3c0a801640190725e63f8ac80` at position `21`.

## Decision

The gate now evaluates whether the pipeline supports the requested capability and whether the story is clear and low-complexity enough. Table names affect risk and metadata lookup, not baseline eligibility.
