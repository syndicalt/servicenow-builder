# Sprint 86 Change Log

## Goal

Move generated implementation handoff from local Update Sets to retrieved Update Sets so generated candidates can be reviewed before commit.

## Changes

- Replaced the model fulfillment handoff target from `sys_update_set` to `sys_remote_update_set`.
- Generated candidate customer updates as `sys_update_xml` rows linked through `remote_update_set`.
- Removed the automated local apply-under-update-set call from model fulfillment, even when the legacy `JEDI_UPDATE_SET_APPLY` setting is present.
- Linked the Story work note to `sys_remote_update_set.do?sys_id=...`.
- Added deterministic XML payload generation for custom `sys_dictionary` changes and their `sys_documentation` field labels.
- Added retrieved Form Layout payload generation for `sys_ui_form` changes by resolving global `rm_story` main Default/Scrum sections and inserting the field below Description in the payload, without mutating the live form.

## Tests

- Added failing coverage proving handoff creates `sys_remote_update_set`, not `sys_update_set`.
- Added coverage proving retrieved customer updates use `remote_update_set` and never local `update_set`.
- Updated model fulfillment coverage to prove no `sys_user_preference`, `sys_dictionary`, or local apply mutation happens after handoff.
- Updated runtime OpenAI coverage for the new retrieved Update Set request sequence.
- Added coverage for retrieved Form Layout updates so form placement is not silently dropped.

## Decision

Generated candidates belong in Retrieved Update Sets. Local Update Sets represent in-instance development work and make generated changes live too early. Retrieved Update Sets preserve the ServiceNow review, preview, scan, conflict resolution, and commit lifecycle.
