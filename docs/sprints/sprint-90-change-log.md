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

## Decision

Generated implementation candidates now enter ServiceNow through the same server-side importer path proven in Sprint 89. Direct Table API writes to `sys_update_xml` are not part of the production handoff path.
