# Sprint 123 Change Log

## Goal

Implement the first declarative UI Policy generation path behind deterministic validators and retrieved Update Set review.
This sprint is the UI Policy generation implementation sprint.

## Changes

- Enabled `ui_policy_generate` with `current_max_story_points=3` while preserving `target_max_story_points=5`.
- Added a UI Policy generation builder for reviewed `sys_ui_policy` and `sys_ui_policy_action` customer updates.
- Added deterministic validators for table-local UI Policy candidates, run-scripts disabled state, script-free payloads, matching action tables, matching action policy names, and ServiceNow tri-state action values.
- Added capability analysis routing so complete UI Policy generation stories can enter automated build.
- Added runtime/model allowlist coverage for `sys_ui_policy` and `sys_ui_policy_action`.
- Updated the operator guide.

## Boundary

The supported subset is declarative form behavior only. forbidden UI Policy behavior includes run scripts, advanced scripts, Client Script behavior, `g_form` logic, Business Rule creation, Script Include creation, Flow creation, ACL changes, integration calls, cross-table behavior, data migration, credentials, secrets, tokens, and API keys.

Retrieved Update Set preview/commit remains the human review boundary.

## Tests

- Added UI Policy handoff coverage proving generated `sys_ui_policy` and `sys_ui_policy_action` customer updates are imported as a retrieved Update Set.
- Added negative handoff coverage proving run-scripts payloads fail closed before import.
- Added model fulfillment coverage proving `ui_policy_generate` candidates flow through provider generation, artifact persistence, retrieved Update Set handoff, and Ready for Testing writeback.
- Kept the project-level 90% coverage gate as the release boundary.
