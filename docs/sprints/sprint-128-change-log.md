# Sprint 128 Change Log

## Flow XML shape repository

Sprint 128 added the Flow XML shape repository `flow-xml-shapes-v1`. This is review metadata only; there is no Flow XML builder.

Changes:

- Added `flow_xml_shape_repository`.
- Added typed shape metadata for `sys_hub_flow`.
- Added typed shape metadata for `sys_hub_action_instance`.
- Added typed shape metadata for `sys_hub_flow_logic_instance_v2`.
- Recorded `record_update` as the required root element.
- Recorded `INSERT_OR_UPDATE` as the only approved action.
- Recorded required fields, forbidden fields, and shape-specific review notes.
- Connected the repository version and shape table list to the Flow builder preflight plan.

Boundary:

The repository does not produce XML. It does not create customer updates. It does not enable retrieved Update Set handoff. It exists so the eventual Flow builder cannot proceed without explicit, reviewed XML shape evidence.

Verification:

- Added failing tests first for repository content and unknown shape lookup.
- Added preflight evidence coverage proving the builder plan sees `flow-xml-shapes-v1`.
- Preserved the 90 percent coverage gate.
