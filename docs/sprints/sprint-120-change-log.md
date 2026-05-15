# Sprint 120 Change Log

## Goal

Implement the first Script Include generation implementation path without coupling reusable server-side utility code to caller generation.

## Changes

- Enabled `script_include_generate` for the narrow utility-only subset.
- Set the current maturity limit to `current_max_story_points=3` while preserving `target_max_story_points=5`.
- Added deterministic `sys_script_include` candidate validation before retrieved Update Set import.
- Added a Script Include XML builder that converts structured provider output into a `sys_script_include` customer update.
- Reused the existing retrieved Update Set handoff so ServiceNow preview/commit remains the human review boundary.
- Expanded the model allowlist to permit `sys_script_include` insert candidates for this capability.

## Supported Boundary

Script Include generation supports one generated server-side utility Script Include, one named class or function, explicit scope, explicit client-callable decision, declared public methods, declared table/field access, and a reviewer test plan.

forbidden Script Include behavior fails closed before import. This includes client-callable Script Includes, global privilege escalation, cross-scope access changes, role/ACL/property/security changes, outbound calls, credentials, secrets, tokens, API keys, destructive GlideRecord mutation, data migration, and bundled caller creation.

## Tests

- Added capability-analysis coverage for complete Script Include generation stories.
- Added handoff coverage proving `sys_script_include` customer updates are imported through retrieved Update Sets.
- Added negative handoff coverage for client-callable Script Includes.
- Added model-fulfillment coverage proving a validated Script Include candidate reaches retrieved Update Set handoff.
- Added documentation tests for the enabled Script Include generation boundary.
