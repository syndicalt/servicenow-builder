# Sprint 18 Change Log

## Writeback Field Discovery

- Added ServiceNow `sys_dictionary` discovery for active `rm_story` fields.
- Added typed dictionary field metadata for element, label, type, and active status.
- Required structured writeback fields before `plan-writeback` can be considered safe.
- Made `plan-writeback` fails closed when required structured writeback fields are missing.

## Required Fields

- `state`
- `u_ai_status`
- `u_ai_build_reference`
- `u_ai_candidate_artifact`

## Safety Boundary

- Kept the command dry-run only.
- Preserved no ServiceNow mutation from the writeback planning path.
- Avoided falling back to comments/work notes as the machine protocol when structured fields are absent.
