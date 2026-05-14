# Sprint 85 Change Log

## Goal

Correct Story form placement so generated Update Set candidates place fields on the visible Story form, not only in the activity Notes tab.

## Changes

- Reproduced the live `STRY0010013` issue against ServiceNow: `rm_story.u_ai_review_notes` existed in `sys_dictionary`, but the field was not present in the Scrum main Story form section.
- Confirmed the previous apply path inserted `sys_ui_element` rows for the Scrum Notes section and the default main section while missing the Scrum main section that contains `description` and `acceptance_criteria`.
- Changed the Update Set apply planner so known Story field placement resolves from global `rm_story` main sections for the Default and Scrum views, then verifies each target section contains the `description` form element.
- Blocked the over-broad anchor-only strategy because `sys_ui_element` lookups can encounter Description-bearing sections outside the Story table boundary.
- Added support for model output using `section_name` as a form-section alias.
- Normalized model field aliases even when the model emits the canonical key with a blank value, such as `element: ""` plus `field_name: "u_ai_review_notes"`.
- Kept ordinary explicit named-section placement for non-specialized custom fields.

## Tests

- Added failing coverage proving a Description-anchored Story field is applied to every global main Story form section discovered through `sys_ui_element`.
- Added coverage proving Description-anchored placement starts from `sys_ui_section name=rm_story` instead of a broad `sys_ui_element` anchor lookup.
- Added failing coverage for blank canonical dictionary keys being repaired from their model aliases before validation.
- Updated existing form-layout tests to reflect the corrected behavior for `u_ai_review_notes`.
- Preserved coverage for named-section placement with a separate custom field.

## Decision

For this story type, the deterministic ServiceNow layout data is the placement authority. Model phrasing can describe intent, but it cannot select an activity/log section when the story asks for a field below Description on the Story form.
