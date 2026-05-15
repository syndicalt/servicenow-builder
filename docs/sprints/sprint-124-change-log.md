# Sprint 124 Change Log

## Goal

Design the Flow Designer generation profile before enabling any Flow Designer mutation.
This sprint is the Flow Designer generation profile design sprint.

## Changes

- Added ADR 0011 for the Flow Designer generation profile.
- Added a designed `flow_modify` capability profile with `current_max_story_points=0` and `target_max_story_points=5`.
- Defined the future Flow Designer artifact boundary across `sys_hub_flow`, `sys_hub_trigger_instance`, `sys_hub_action_instance`, and `sys_hub_flow_logic_instance_v2`.
- Required future `flows` and `flow_graph` context before any model call can support Flow mutation.
- Updated the operator guide and production hardening backlog.

## Boundary

No runtime generation is enabled. Flow Designer remains context-only until graph retrieval, graph diff validation, and retrieved Update Set XML evidence exist.

## Tests

- Added capability registry coverage for the designed Flow Designer profile.
- Added documentation coverage for ADR 0011, the operator guide, the sprint changelog, and the backlog.
