# Sprint 91 Change Log

## Goal

Move a story to Ready for Testing after the generated retrieved Update Set handoff is created.

## Changes

- Changed `create_update_set_handoff()` so the post-import story update includes the discovered `Ready for Testing` state value.
- Set `u_ai_status=Ready for Testing` in the same story update as the retrieved Update Set work note.
- Reused active `rm_story.state` choice discovery instead of hardcoding the PDI value `-7`.
- Kept preview, scan, problem resolution, and commit as human ServiceNow review actions on the retrieved Update Set.

## Tests

- Updated handoff tests to prove the story update includes `state=-7`, `u_ai_status=Ready for Testing`, and the retrieved Update Set work note when the PDI exposes `Ready for Testing` as `-7`.
- Updated model fulfillment tests to cover the same post-handoff state transition.
- Updated runtime OpenAI coverage to prove the worker fetches `sys_choice` for `rm_story.state` before writing the Ready for Testing story update.

## Decision

Ready for Testing now means the automated implementation handoff exists and is ready for human review/testing in ServiceNow. It does not replace the retrieved Update Set preview/commit approval boundary.
