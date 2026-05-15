# Sprint 119 Change Log

## Goal

Design the Script Include generation profile design boundary before enabling reusable server-side code mutation.

## Changes

- Added ADR 0009 for `script_include_generate`.
- Moved the `script_include_generate` capability profile from `planned` to `designed`.
- Kept `current_max_story_points=0` for Script Include generation because runtime mutation is not enabled.
- Kept the full-maturity target at `target_max_story_points=5`.
- Defined the first supported `sys_script_include` subset: one server-side utility Script Include, one named class or function, explicit scope, explicit client-callable decision, and no simultaneous caller creation.
- Documented forbidden cases including global privilege escalation, cross-scope access changes, role/ACL/property changes, credentials, secrets, tokens, API keys, outbound calls, broad GlideRecord mutation, data migration, background repair logic, and bundled caller generation.
- Added Sprint 120 as the implementation sprint for `script_include_generate`.

## Decision

No runtime generation is enabled for Script Includes in Sprint 119. The next implementation must generate reviewed `sys_script_include` / `sys_update_xml` retrieved Update Set handoffs only after deterministic validators approve the structured output.

## Tests

- Added capability profile coverage for the designed-but-disabled Script Include generation profile.
- Added ADR documentation coverage for the mutation boundary.
- Added operator-guide coverage for supported and forbidden Script Include generation behavior.
- Added production-backlog coverage for Sprint 119 and Sprint 120.
