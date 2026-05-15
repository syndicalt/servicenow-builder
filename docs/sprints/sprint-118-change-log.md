# Sprint 118 Change Log

## Goal

Implement the first Client Script generation implementation path without bypassing ServiceNow review.

## Changes

- Enabled `client_script_generate` for the narrow table-local subset.
- Set the current maturity limit to `current_max_story_points=3` while preserving `target_max_story_points=5`.
- Added deterministic `sys_script_client` candidate validation before retrieved Update Set import.
- Added a Client Script XML builder that converts structured provider output into a `sys_script_client` customer update.
- Reused the existing retrieved Update Set handoff so ServiceNow preview/commit remains the human review boundary.
- Expanded the model allowlist to permit `sys_script_client` insert candidates for this capability.
- Kept Script Include generation planned only.

## Supported Boundary

Client Script generation supports one generated script on one target table, `onLoad`, `onChange`, or `onSubmit` type, optional target field for `onChange`, declared fields read, declared fields written, messages shown, and a reviewer test plan.

Forbidden Client Script behavior fails closed before import. This includes DOM access outside `g_form`, raw browser globals, browser storage, network calls, endpoints, credentials, secrets, tokens, API keys, and GlideAjax dependency creation.

## Tests

- Added capability-analysis coverage for complete Client Script generation stories.
- Added handoff coverage proving `sys_script_client` customer updates are imported through retrieved Update Sets.
- Added negative handoff coverage for forbidden Client Script browser and network APIs.
- Added model-fulfillment coverage proving a validated Client Script candidate reaches retrieved Update Set handoff.
- Added documentation tests for the enabled Client Script generation boundary.
