# Sprint 126 Change Log

## Flow graph diff contract

Sprint 126 added validation-only Flow Designer graph diff support. No runtime generation is enabled.

Changes:

- Added the `sys_hub_flow_graph_diff` pseudo-table contract for future `flow_modify` provider output.
- Allowed only narrow `add_action` and `update_condition` diff operations.
- Required the diff to include flow identity, target table, trigger summary, existing graph hash, affected nodes, affected edges, test plan, rollback notes, and reviewer notes.
- Rejected raw XML and raw `sys_update_xml` in Flow graph diff output.
- Rejected unretrieved node references, broad graph rewrites, scripts, custom actions, spokes, credentials, tokens, subflows, approvals, and external endpoints.
- Confirmed retrieved Update Set handoff still rejects `sys_hub_flow_graph_diff`.

Boundary:

This sprint validates model output shape only. It does not create Flow Designer customer updates and does not import retrieved Update Sets for Flow Designer. The next Flow sprint should design the builder only after this contract remains stable under UAT examples.

Verification:

- Added failing tests first for valid graph diff acceptance and forbidden graph diff rejection.
- Added a handoff guard test proving validation-only Flow output cannot be imported.
- Preserved the 90 percent coverage gate.
