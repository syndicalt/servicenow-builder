# ADR 0008: Client Script Generation Profile

## Status

Accepted.

## Context

Sprint 113 generalized code-surface analysis for Business Rules, Client Scripts, and Script Includes. Sprint 116 enabled the first Business Rule generation path only after a narrow profile, deterministic validators, and retrieved Update Set handoff were in place.

Client Script generation is the next code-surface mutation candidate. It changes browser-side ServiceNow behavior and can easily become unsafe if the model creates arbitrary DOM manipulation, hidden network calls, or unreviewed GlideAjax dependencies. The first profile must therefore be explicit before runtime generation is enabled.

## Decision

Define the future `client_script_generate` capability profile. No runtime generation is enabled by this ADR.

The first supported subset is:

- table-local Client Scripts only.
- one generated `sys_script_client` record per story.
- `onLoad`, `onChange`, or `onSubmit` only.
- active scripts on a single target table.
- optional target field for `onChange`.
- client behavior implemented with ServiceNow client APIs, primarily `g_form`.
- no raw DOM access.
- no external network calls.
- no creation of GlideAjax dependencies or Script Includes.
- generated changes must be represented as `sys_script_client` customer updates inside `sys_update_xml`.
- Retrieved Update Set preview/commit remains the human review boundary.

The forbidden cases are:

- DOM manipulation outside `g_form` APIs.
- `document`, `window`, `XMLHttpRequest`, `fetch`, browser storage APIs, or endpoint construction.
- GlideAjax dependency creation.
- credentials, secrets, tokens, API keys, usernames, or passwords.
- cross-table data writes.
- ACL, UI Policy, Business Rule, Script Include, Flow Designer, or integration changes.
- hiding required fields or weakening validation without explicit acceptance criteria.
- direct mutation of system tables outside the generated `sys_script_client` customer update.

## Output Schema

The future provider output must be a structured object, not free-form XML:

- `capability`: `client_script_generate`.
- `target_table`.
- `script_name`.
- `client_script_type`: `onLoad`, `onChange`, or `onSubmit`.
- `field_name` for `onChange`, otherwise empty.
- `condition_summary`.
- `script_body`.
- `fields_read`.
- `fields_written`.
- `messages_shown`.
- `test_plan`.
- `rollback_notes`.
- `reviewer_notes`.

The builder converts validated structured output into retrieved Update Set XML. The provider must not provide raw `sys_update_xml` as the authoritative artifact.

## Deterministic Validators

The `client_script_generate` profile must fail closed unless all deterministic validators pass:

- target table exists in retrieved `sys_db_object`.
- target table matches the retrieved `client_scripts` context.
- Client Script type is `onLoad`, `onChange`, or `onSubmit`.
- `onChange` names an existing field on the target table.
- generated script uses approved ServiceNow client APIs such as `g_form`.
- generated script has no raw DOM, browser storage, network calls, endpoints, credentials, secrets, tokens, or API keys.
- generated script writes only approved fields named in the story.
- generated `sys_script_client` XML contains required fields and no forbidden fields.
- generated retrieved Update Set XML can be parsed and references only the intended `sys_script_client` customer update.

## UAT story shape

A story eligible for future Client Script generation must name:

- target table.
- Client Script type: `onLoad`, `onChange`, or `onSubmit`.
- target field for `onChange`.
- explicit condition or trigger behavior.
- expected client-side behavior.
- fields that may be read.
- fields that may be written.
- messages shown to the user, if any.
- test record setup.
- observable acceptance criteria.
- rollback expectation.

If any required detail is missing, the story routes to clarification. If forbidden behavior is requested, the story routes to human review or manual developer build.

## Consequences

- Sprint 118 can implement `client_script_generate` without inventing the mutation boundary during coding.
- The product continues to use ServiceNow-native retrieved Update Set preview/commit for human review.
- Client Script generation does not imply UI Policy, Business Rule, Script Include, Flow Designer, ACL, integration, or data migration generation.
