# Sprint 117 Change Log

## Goal

Design the Client Script generation profile design boundary before enabling any new browser-side ServiceNow automation.

## Changes

- Added ADR 0008 for `client_script_generate`.
- Moved the `client_script_generate` capability profile from `planned` to `designed`.
- Kept `current_max_story_points=0` for Client Script generation because runtime mutation is not enabled.
- Kept the full-maturity target at `target_max_story_points=5`.
- Defined the first supported `sys_script_client` subset: one table-local Client Script, `onLoad`, `onChange`, or `onSubmit`, optional target field for `onChange`, and behavior through ServiceNow client APIs such as `g_form`.
- Documented forbidden cases including DOM manipulation outside `g_form` APIs, raw browser globals, browser storage, network calls, endpoints, credentials, secrets, tokens, API keys, GlideAjax dependency creation, and unrelated platform mutation.
- Added Sprint 118 as the implementation sprint for `client_script_generate`.

## Decision

No runtime generation is enabled for Client Scripts in Sprint 117. The next implementation must generate reviewed `sys_script_client` / `sys_update_xml` retrieved Update Set handoffs only after deterministic validators approve the structured output.

## Tests

- Added capability profile coverage for the designed-but-disabled Client Script generation profile.
- Added ADR documentation coverage for the mutation boundary.
- Added operator-guide coverage for supported and forbidden Client Script generation behavior.
- Added production-backlog coverage for Sprint 117 and Sprint 118.
