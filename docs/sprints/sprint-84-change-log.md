# Sprint 84 Change Log

## Goal

Generate ServiceNow customer updates for reviewed AI candidates without fabricating `sys_update_xml` rows.

## Changes

- Added `update_set_apply` as the controlled apply-under-update-set service.
- Added a ServiceNow table-list read path so the worker can verify captured `sys_update_xml` rows after applying supported changes.
- Added `JEDI_UPDATE_SET_APPLY` and `JEDI_UPDATE_SET_USER_NAME` runtime controls.
- Wired model fulfillment so the worker can create the Update Set handoff, set the integration user's current Update Set, apply supported dictionary and form-layout changes, verify customer updates, and write a follow-up story work note.
- Added deterministic `rm_story` form placement through native `sys_ui_element` records.
- Defaulted `rm_story` form placement to the existing Notes section when the model omits a section.
- Normalized model output aliases for the known AI Review Notes field, including `field_name`, `field_label`, `help_text`, `hint`, and XML-shaped form element snippets.
- Treated placeholder model sys_ids such as `[FORM_SYS_ID_HERE]` as absent before validation.
- Kept unsupported candidate changes fail-closed before mutation.
- Verified the live `STRY0010013` run generated three ServiceNow customer updates in the handoff Update Set.

## Tests

- Added unit coverage proving dictionary changes are applied only after selecting the handoff Update Set for the integration user.
- Added unit coverage proving form placement creates native UI element updates in the Notes section.
- Added unit coverage for model alias normalization, known field metadata defaults, XML form snippets, and placeholder sys_id handling.
- Added guardrail coverage proving unsupported tables fail before any ServiceNow mutation.
- Added coverage proving the app reads `sys_update_xml` for verification and never writes it directly.
- Added runtime setting coverage for the new update-set apply controls.

## Decision

Customer updates must be platform-generated. The application may select the current Update Set and perform allowlisted ServiceNow mutations, but it must not insert synthetic `sys_update_xml`. This preserves native Update Set Preview/Scan/Commit behavior and keeps the review surface inside ServiceNow.
