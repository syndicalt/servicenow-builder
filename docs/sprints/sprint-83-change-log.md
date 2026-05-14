# Sprint 83 Change Log

## Goal

Move the generated candidate review surface into ServiceNow by creating a native Update Set handoff record and linking it from the story.

## Changes

- Added `update_set_handoff` with a typed `create_update_set_handoff()` service.
- Create or update a `sys_update_set` record named `JEDI <story number> - AI Candidate`.
- Write the candidate artifact ref, candidate hash, confidence, risk score, proposed change summary, and reviewer notes into the Update Set description.
- Link the story to the Update Set through a work note with a direct `sys_update_set.do?sys_id=...` URL.
- Added a post-artifact-persistence callback to fulfillment results so ServiceNow handoff runs only after the candidate JSON artifact exists in PostgreSQL.
- Updated model fulfillment to create the ServiceNow Update Set handoff after the `implementation_candidate` artifact is persisted.

## Verification

- Added unit coverage for native Update Set handoff creation and rejected candidate guardrails.
- Added worker coverage proving post-persistence callbacks receive DB artifact refs and failed callbacks fail the job instead of marking it complete.
- Updated runtime OpenAI coverage to verify the hosted flow creates a `sys_update_set` record and writes a story work note containing the durable candidate artifact ref.

## Architecture Notes

The Update Set is now the intended user-facing handoff in ServiceNow. The DB-backed candidate JSON remains audit evidence and source context. This sprint intentionally does not fabricate `sys_update_xml` rows or auto-commit Update Sets. The next engineering step is a controlled apply-under-update-set path for allowlisted candidate changes, so the handoff can become commit-ready without bypassing ServiceNow review.
