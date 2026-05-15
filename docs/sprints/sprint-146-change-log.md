# Sprint 146 Change Log

## Dictionary/form typed intent alias hardening

- Live UAT of `STRY0010020` showed that `Target artifact type: Dictionary field and form placement` was not mapped to the dictionary/form capability.
- `AutomationIntent` now recognizes dictionary/form aliases including `Dictionary field`, `Dictionary field and form placement`, `Field and form placement`, and `Form field`.
- Structured placement fields now support `Placement anchor:` and `Placement position:` lines.
- `Placement position: after Description` normalizes to below `description`, matching the existing form placement contract.
- The STRY0010020 typed intent now routes to `dictionary_field_create`, `field_label_create`, and `form_layout_place_field` instead of `unknown`.
