# Sprint 113 Change Log

## Goal

Code surface analysis capability: generalize Business Rule analysis into the same read-only pattern for Business Rules, Client Scripts, and Script Includes.

## Changes

- Added `client_script_analyze` and `script_include_analyze` context-only capabilities.
- Kept `business_rule_analyze` but moved runtime output to the shared `code-surface-analysis-v1` artifact shape.
- Added CapabilityProfile entries for `sys_script`, `sys_script_client`, and `sys_script_include`.
- Extended deterministic story analysis for Client Script and Script Include stories.
- Kept Script Include analysis global because Script Includes are not table-bound in the same way as Business Rules and Client Scripts.
- Reused ServiceNow surface discovery and redaction for all three code surfaces.
- Replaced the Business Rule-specific runtime artifact with `code_surface_analysis`.
- Kept model invocation and retrieved Update Set handoff disabled for code-surface analysis.

## Decision

No new mutation surface was added. Code surface generation remains unsupported until each artifact type has its own mutation profile, deterministic validators, XML evidence, and UAT expectations.

## Tests

- Added capability profile tests for Business Rules, Client Scripts, and Script Includes.
- Added capability analyzer tests for Client Script and Script Include context analysis.
- Added model fulfillment tests proving no model call, no Update Set import, redacted code-surface context, and human-review feedback.
- Added documentation tests for the shared code surface analysis contract.
