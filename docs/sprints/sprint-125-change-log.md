# Sprint 125 Change Log

## Flow graph retrieval hardening

Sprint 125 made Flow Designer graph context a first-class, read-only prerequisite for future `flow_modify` work. No runtime generation is enabled.

Changes:

- Added `flow_graph` to the ServiceNow surface context model.
- Retrieved graph records from `sys_hub_trigger_instance`, `sys_hub_action_instance`, and `sys_hub_flow_logic_instance_v2`.
- Retrieved input and output schema records from `sys_hub_trigger_input`, `sys_hub_trigger_output`, `sys_hub_action_input`, and `sys_hub_action_output`.
- Added citations and evidence for every graph table query.
- Made required Flow graph context fail closed when the target flow list is missing or when a flow has no trigger or action graph records.
- Kept Flow Designer mutation disabled. This sprint only hardens the researcher layer needed before any future graph diff builder exists.

Verification:

- Added failing tests first for complete graph retrieval and incomplete graph failure.
- Updated fulfillment tests so missing Flow context includes both `flows` and `flow_graph`.
- Preserved the 90 percent coverage gate.
