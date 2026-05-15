# Sprint 96 Change Log

## Goal

Make AI story metadata system-owned and align structured fields with the retrieved Update Set handoff path.

## Changes

- Kept `u_ai_status` as the primary visible automation state.
- Added read-only bootstrap metadata for:
  - `u_ai_handoff_type`
  - `u_ai_handoff_reference`
  - `u_ai_artifact_reference`
- Changed bootstrap field creation to send `read_only=true` for AI operational fields.
- Changed bootstrap apply to patch existing required AI operational dictionary fields to `read_only=true` when they already exist.
- Changed retrieved Update Set handoff writeback to populate:
  - `u_ai_status=Ready for Testing`
  - `u_ai_handoff_type=retrieved_update_set`
  - `u_ai_handoff_reference=<sys_remote_update_set sys_id>`
  - `u_ai_artifact_reference=<db artifact reference>`
- Kept `u_ai_build_reference` and `u_ai_candidate_artifact` as required fields for the legacy external-build writeback command, while moving retrieved Update Set handoff metadata to handoff-specific fields.

## Tests

- Updated bootstrap planning and apply tests for the new read-only fields.
- Updated ServiceNow client tests to verify `read_only=true` is sent when creating story dictionary fields.
- Updated retrieved Update Set handoff and model fulfillment tests to verify structured handoff fields are populated.
- Updated CLI bootstrap tests for the new required field set.
- Added bootstrap tests for read-only remediation of existing fields.

## Decision

`u_ai_build_reference` and `u_ai_candidate_artifact` are legacy external-build fields. They should not be deleted from existing instances yet, but new retrieved Update Set fulfillment should use handoff-specific metadata instead. This sprint originally used dictionary `read_only=true` to keep users from manually editing AI operational fields.

Sprint 141 supersedes that dictionary-level read-only decision. AI operational fields must be dictionary-writable so the integration identity can persist runtime state and handoff metadata through the Table API. Human read-only behavior belongs in form policy, UI policy, ACLs, or role-scoped controls that still allow automation writes.
