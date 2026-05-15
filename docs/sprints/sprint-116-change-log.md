# Sprint 116 Change Log

## Goal

Implement the first Business Rule generation implementation path without weakening the ServiceNow review boundary.

## Changes

- Enabled `business_rule_generate` for the narrow table-local subset.
- Kept the current maturity limit at `current_max_story_points=3` while preserving the full-maturity target of `target_max_story_points=5`.
- Added deterministic `sys_script` candidate validation before retrieved Update Set import.
- Added a Business Rule XML builder that converts structured provider output into a `sys_script` customer update.
- Reused the existing retrieved Update Set handoff so ServiceNow preview/commit remains the human review boundary.
- Expanded the model allowlist to permit `sys_script` insert candidates for this capability.
- Kept Client Script and Script Include generation planned only.

## Supported Boundary

Business Rule generation supports one generated rule on one target table, `before` or `after` timing, `insert` and/or `update` operations, an explicit condition, declared fields read, declared fields written, and a reviewer test plan.

Forbidden Business Rule script behavior fails closed before import. This includes `GlideRecord`, destructive update/delete APIs, `setWorkflow(false)`, events, outbound REST/SOAP calls, endpoints, credentials, passwords, tokens, and API keys.

## Tests

- Added capability-analysis coverage for complete Business Rule generation stories.
- Added handoff coverage proving `sys_script` customer updates are imported through retrieved Update Sets.
- Added negative handoff coverage for forbidden Business Rule script tokens.
- Added model-fulfillment coverage proving a validated Business Rule candidate reaches retrieved Update Set handoff.
- Added documentation tests for the enabled Business Rule generation boundary.
