# Sprint 148 Change Log

## Business Rule structured story hardening

- Live UAT of `STRY0010021` showed that a structured Business Rule story using `Timing: before` was routed to clarification.
- `AutomationIntent` now accepts `Timing:` and `When:` as aliases for `Trigger timing:`.
- Business Rule metadata now treats `Fields written / affected:` as satisfying required `fields written` details.
- The STRY0010021 path now remains scoped to `business_rule_generate` and `sys_script` retrieved Update Set handoff.
