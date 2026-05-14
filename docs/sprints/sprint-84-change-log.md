# Sprint 84 Change Log

## Goal

Generate ServiceNow customer updates for reviewed AI candidates without fabricating `sys_update_xml` rows.

## Changes

- Added `update_set_apply` as the controlled apply-under-update-set service.
- Added a ServiceNow table-list read path so the worker can verify captured `sys_update_xml` rows after applying supported changes.
- Added `JEDI_UPDATE_SET_APPLY` and `JEDI_UPDATE_SET_USER_NAME` runtime controls.
- Wired model fulfillment so the worker can create the Update Set handoff, set the integration user's current Update Set, apply supported dictionary changes, verify customer updates, and write a follow-up story work note.
- Kept unsupported candidate changes fail-closed before mutation. Form layout edits are not applied until a deterministic ServiceNow form-layout implementation exists.

## Tests

- Added unit coverage proving dictionary changes are applied only after selecting the handoff Update Set for the integration user.
- Added guardrail coverage proving unsupported tables fail before any ServiceNow mutation.
- Added coverage proving the app reads `sys_update_xml` for verification and never writes it directly.
- Added runtime setting coverage for the new update-set apply controls.

## Decision

Customer updates must be platform-generated. The application may select the current Update Set and perform allowlisted ServiceNow mutations, but it must not insert synthetic `sys_update_xml`. This preserves native Update Set Preview/Scan/Commit behavior and keeps the review surface inside ServiceNow.
