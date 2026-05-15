# ADR 0007: Business Rule Generation Profile

## Status

Accepted.

## Context

Sprint 112 introduced Business Rule analysis and Sprint 113 generalized code-surface analysis for Business Rules, Client Scripts, and Script Includes. That analysis layer is intentionally read-only. It retrieves live ServiceNow context, redacts script-like material, stores evidence, and routes the story to human review.

Business Rule generation is the first code-surface mutation candidate, but it changes executable server-side ServiceNow behavior. Treating it as a simple extension of analysis would be unsafe. The first mutation profile must be narrow, deterministic, and reviewable through retrieved Update Sets.

## Decision

Define a future `business_rule_generate` capability profile. No runtime generation is enabled by this ADR.

The first supported subset is:

- table-local Business Rules only.
- `before/after` timing only.
- `insert/update` actions only.
- explicit condition required.
- simple field assignment, work note/comment update, or abort message only.
- one target table per story.
- one Business Rule per generated candidate.
- generated changes must be represented as `sys_script` customer updates inside `sys_update_xml`.
- Retrieved Update Set preview/commit remains the human review boundary.

The forbidden cases are:

- delete rules.
- async or display rules.
- scheduled jobs.
- global scripts or Script Include creation.
- ACL changes.
- outbound REST, SOAP, email, event, or integration calls.
- credentials, secrets, tokens, API keys, or endpoint construction.
- cross-table writes.
- broad GlideRecord query/update/delete patterns.
- encoded query construction from story text.
- direct mutation of system tables outside the generated `sys_script` customer update.

## Output Schema

The future model/provider output must be a structured object, not free-form XML:

- `capability`: `business_rule_generate`.
- `target_table`.
- `rule_name`.
- `when`: `before` or `after`.
- `operations`: `insert`, `update`, or both.
- `condition_summary`.
- `condition_expression`.
- `script_body`.
- `fields_read`.
- `fields_written`.
- `test_plan`.
- `rollback_notes`.
- `reviewer_notes`.

The builder converts validated structured output into retrieved Update Set XML. The provider must not provide raw `sys_update_xml` as the authoritative artifact.

## Deterministic Validators

The `business_rule_generate` profile must fail closed unless all deterministic validators pass:

- target table exists in retrieved `sys_db_object`.
- target table matches the analyzed `code-surface-analysis-v1` context.
- condition is present and references fields available in retrieved table schema.
- timing is `before` or `after`.
- operations are limited to `insert` and `update`.
- generated script has no `GlideRecord`, `deleteRecord`, `deleteMultiple`, `updateMultiple`, `setWorkflow(false)`, `gs.eventQueue`, `sn_ws`, REST/SOAP calls, email APIs, credential access, or endpoint strings.
- generated script writes only approved fields named in the story.
- generated script contains no secrets, tokens, usernames, passwords, or API keys.
- generated `sys_script` XML contains required fields and no forbidden fields.
- generated retrieved Update Set XML can be parsed and references only the intended `sys_script` customer update.

## UAT Story Shape

This is the required UAT story shape.

A story eligible for future Business Rule generation must name:

- target table.
- Business Rule timing: before or after.
- trigger operations: insert and/or update.
- explicit condition.
- expected behavior.
- fields that may be read.
- fields that may be written.
- test record setup.
- observable acceptance criteria.
- rollback expectation.

If any of those are missing, the story routes to clarification. If forbidden behavior is requested, the story routes to human review or manual developer build.

## Consequences

- Sprint 115 can implement the profile and validators without reopening the safety boundary.
- The model can help produce structured implementation intent, but deterministic code owns validation and XML construction.
- The product still uses ServiceNow-native preview/commit for human review.
- Business Rule generation does not imply Client Script, Script Include, Flow Designer, ACL, integration, or data migration generation.
