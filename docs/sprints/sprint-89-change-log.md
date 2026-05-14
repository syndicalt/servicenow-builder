# Sprint 89 Change Log

## Goal

Bootstrap a reviewed ServiceNow-side Update Set XML importer instead of automating the `upload.do` UI path.

## Changes

- Added `build_update_set_importer_bootstrap_spec()` for a Scripted REST API importer.
- Added `update_set_importer_servicenow_record_plan()` with explicit `sys_ws_definition` and `sys_ws_operation` records.
- Added `apply-update-set-importer` with `--confirm-service-id jedi_update_set_import` and `--confirm-records` gates.
- Added `verify-update-set-importer` for read-only verification of installed Scripted REST records.
- The importer operation validates `update_set_xml` and calls `GlideUpdateManager2().loadXML(xmlPayload)` server-side.

## Tests

- Added bootstrap tests for the Scripted REST spec, record plan, apply confirmation, apply ordering, and verification.
- Added CLI tests for planning and applying the importer bootstrap.
- Added documentation coverage for the operator workflow.
- Added client coverage for discovering the installed importer operation URI and posting XML to it.

## Smoke

- Applied the importer to the PDI and verified `sys_ws_definition` plus `sys_ws_operation`.
- Confirmed the endpoint fails closed with `400 update_set_xml_required` when no XML is supplied.
- Posted minimal reviewed XML to `/api/1860704/jedi_update_set_import`.
- Verified ServiceNow created retrieved update set `JEDI XML Import Smoke 20260514 002` with sys_id `64c3e9d1b27a42479620114da017857a`, state `loaded`, and zero customer update rows.

## Decision

Do not automate `upload.do` from the sidecar. The production path should use a reviewed ServiceNow-side Scripted REST importer so XML loading happens inside ServiceNow using platform update set mechanics. CICD preview and commit remain separate later lifecycle steps.
