# ADR 0009: Script Include Generation Profile

## Status

Accepted.

## Context

Script Includes are reusable server-side JavaScript. They can be powerful implementation units, but they also create broad blast radius if generated carelessly. A generated Script Include can be called by many Business Rules, Client Scripts through GlideAjax, Flow actions, integrations, or background jobs. That makes the first mutation profile materially riskier than a table-local Business Rule or Client Script.

The product should still support Script Include generation eventually because many 3-5 point ServiceNow stories need shared server-side utility logic. The boundary must be explicit before runtime generation is enabled.

## Decision

Define the future `script_include_generate` capability profile. No runtime generation is enabled by this ADR.

The first supported subset is:

- server-side utility Script Includes only.
- one generated `sys_script_include` record per story.
- one named class or function with no inheritance.
- scoped or Global record only when the target scope is explicit.
- inactive-by-default is preferred unless the story requires immediate use.
- no Client Callable behavior unless the story explicitly asks for GlideAjax support and the implementation sprint supports it.
- no creation of callers such as Business Rules, Client Scripts, Flow actions, scheduled jobs, or integrations in the same candidate.
- generated changes must be represented as `sys_script_include` customer updates inside `sys_update_xml`.
- Retrieved Update Set preview/commit remains the human review boundary.

The forbidden cases are:

- global privilege escalation.
- cross-scope access changes.
- role, ACL, property, credential, or system security changes.
- outbound REST, SOAP, email, event, or integration calls.
- credentials, secrets, tokens, API keys, usernames, or passwords.
- broad GlideRecord query/update/delete patterns.
- data migration or background repair logic.
- Script Include changes that require simultaneous caller creation.
- direct mutation of system tables outside the generated `sys_script_include` customer update.

## Output Schema

The future provider output must be a structured object, not free-form XML:

- `capability`: `script_include_generate`.
- `script_include_name`.
- `api_name`.
- `scope`.
- `client_callable`.
- `active`.
- `description`.
- `script_body`.
- `public_methods`.
- `fields_read`.
- `fields_written`.
- `tables_read`.
- `tables_written`.
- `test_plan`.
- `rollback_notes`.
- `reviewer_notes`.

The builder converts validated structured output into retrieved Update Set XML. The provider must not provide raw `sys_update_xml` as the authoritative artifact.

## Deterministic Validators

The `script_include_generate` profile must fail closed unless all deterministic validators pass:

- required Script Include context is retrieved.
- Script Include name and API name are valid ServiceNow identifiers.
- generated script defines exactly the requested class or function.
- generated script has no outbound calls, endpoints, credentials, secrets, tokens, or API keys.
- generated script has no destructive GlideRecord update/delete patterns.
- generated script does not change roles, ACLs, properties, credentials, scheduled jobs, flows, or integrations.
- `client_callable=true` is rejected until GlideAjax generation support is separately implemented.
- generated `sys_script_include` XML contains required fields and no forbidden fields.
- generated retrieved Update Set XML can be parsed and references only the intended `sys_script_include` customer update.

## UAT story shape

A story eligible for future Script Include generation must name:

- Script Include name.
- whether the record is scoped or Global.
- whether it is client callable.
- expected public method or function signature.
- expected server-side behavior.
- tables and fields that may be read.
- tables and fields that may be written.
- caller expectations, if any.
- test data setup.
- observable acceptance criteria.
- rollback expectation.

If any required detail is missing, the story routes to clarification. If forbidden behavior is requested, the story routes to human review or manual developer build.

## Consequences

- Sprint 120 can implement `script_include_generate` without inventing the mutation boundary during coding.
- Script Include generation remains separate from Business Rule, Client Script, Flow Designer, ACL, integration, and data migration generation.
- The first implementation should be conservative and may produce inactive Script Includes for human review before caller wiring is automated.
