# Sprint 76 Change Log

## Goal

Install and verify the ServiceNow lifecycle webhook emitter against the public Railway API endpoint.

## Changes

- Corrected lifecycle webhook bootstrap field mapping for ServiceNow outbound REST Message records.
- Wrote the endpoint to `rest_endpoint` instead of a non-persisted `endpoint` field.
- Resolved the `sys_rest_message_fn.rest_message` parent reference from the installed REST Message `sys_id`.
- Removed `content_type` from the REST method record plan because the PDI table does not persist that field for this method.
- Normalized ServiceNow boolean strings and reference `{value, link}` responses during webhook verification.
- Documented the PDI-only `no_authentication` posture and the requirement for authenticated inbound webhook protection before non-PDI use.

## Verification

- Generated a reviewed lifecycle webhook spec for `https://jedi-devproject-0-jedi.up.railway.app/lifecycle/events`.
- Applied the planned ServiceNow records with explicit `rm_story` confirmation.
- Verified the installed `sys_rest_message`, `sys_rest_message_fn`, and `sys_script` records against the reviewed spec.
- Added regression tests for ServiceNow REST endpoint mapping, method parent resolution, boolean normalization, and reference normalization.

## Architecture Notes

The public Railway API is now reachable by ServiceNow, and the PDI has the outbound REST Message plus `rm_story` after-update Business Rule installed. The next lifecycle test should come from a real PDI `Draft` to `Ready` transition so the emitted event, persisted job, and worker claim all share live story state.
