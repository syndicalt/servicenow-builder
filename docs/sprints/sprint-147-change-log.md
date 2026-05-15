# Sprint 147 Change Log

## Script Include structured story hardening

- Live UAT of `STRY0010023` showed that a structured Script Include story using `Fields written / affected: none` was routed to clarification.
- `AutomationIntent` now treats `Fields written / affected:` as satisfying Script Include `fields written` metadata.
- Script Include stories now keep `script_includes` as the required ServiceNow context surface even when the story is incomplete.
- This prevents broad fallback discovery from incorrectly requiring `form_sections`, `form_layout`, or integration context for Script Include generation.
- The STRY0010023 path now remains scoped to `script_include_generate` and `sys_script_include` Update Set handoff.
- Script Include handoff now deterministically derives `api_name` as `global.<Script Include name>` when the model omits it.
- Explicit non-global or mismatched Script Include metadata is still rejected by the handoff validator.
