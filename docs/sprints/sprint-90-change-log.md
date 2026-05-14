# Sprint 90 Change Log

## Goal

Route model fulfillment handoff through the proven ServiceNow Update Set XML importer instead of direct Table API writes to retrieved update set tables.

## Changes

- Changed `create_update_set_handoff()` to generate full Update Set XML and call `import_update_set_xml(service_id="jedi_update_set_import")`.
- Kept generated customer updates linked through `remote_update_set` inside the XML payload.
- Removed direct runtime upserts to `sys_remote_update_set` and `sys_update_xml` from the generated candidate handoff path.
- Added post-import lookup by `remote_sys_id` before writing the story work note.
- Kept runtime promotion stopped at review handoff; no preview or commit is run by fulfillment.

## Tests

- Updated handoff tests to prove XML is posted to the importer and no Table API upserts are used for update set rows.
- Updated model fulfillment tests to prove legacy `JEDI_UPDATE_SET_APPLY` still does not trigger local mutation.
- Updated runtime OpenAI coverage for importer operation discovery, XML POST, retrieved update set lookup, and story work note link.

## Live Verification

After deploying worker commit `e0f6536`, `STRY0010013` was restaged from Draft (`-6`) to Ready (`1`) to emit a normal lifecycle event. The worker claimed the story, generated model-backed implementation artifacts, imported the generated Update Set XML through `jedi_update_set_import`, and wrote the retrieved Update Set link back to story work notes.

The retrieved Update Set is `JEDI STRY0010013 - AI Candidate`, sys_id `ca51627e2d96dbc3f5c418bfd34821b2`. ServiceNow created four retrieved customer updates linked by `remote_update_set` with no local `update_set` value:

- `sys_dictionary_rm_story_u_ai_review_notes`
- `sys_ui_section_8757b94d7f0000011c1ae8aa30062c20`
- `sys_ui_section_6dc409c57f0000016dd1fbecc461c7b9`
- `sys_documentation_rm_story_u_ai_review_notes_en`

The story work note was written at `2026-05-14 14:37:07` UTC. The field and form placement were confirmed in the PDI. The retrieved Update Set state reported as `committed` after the run, and the dictionary field `rm_story.u_ai_review_notes` showed `sys_updated_on=2026-05-14 14:37:32` by `admin`; this means the review/commit boundary needs an explicit production control before this path is considered production-safe.

## Decision

Generated implementation candidates now enter ServiceNow through the same server-side importer path proven in Sprint 89. Direct Table API writes to `sys_update_xml` are not part of the production handoff path.
