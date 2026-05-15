# ADR 0010: UI Policy Generation Profile

## Status

Accepted.

## Context

UI Policies are a natural next ServiceNow automation surface after dictionary/form, Business Rule, Client Script, and Script Include support. They are usually safer than Client Scripts for form behavior because they express field state changes declaratively through `sys_ui_policy` and `sys_ui_policy_action`.

They still need a separate mutation profile. UI Policies can include scripts, target specific views, interact with form sections, and change mandatory, visible, and read-only behavior in ways that affect data entry. The automation must not silently turn a declarative field-state story into client-side scripting or security behavior.

## Decision

Define the future `ui_policy_generate` capability profile. No runtime generation is enabled by this ADR.

The first supported subset is:

- table-local UI Policies only.
- one generated `sys_ui_policy` record per story.
- one or more `sys_ui_policy_action` records tied to that generated policy.
- explicit target table.
- explicit condition.
- explicit reverse-if-false decision.
- field actions limited to mandatory, visible, or read-only behavior.
- generated changes must be represented as `sys_ui_policy` and `sys_ui_policy_action` customer updates inside `sys_update_xml`.
- Retrieved Update Set preview/commit remains the human review boundary.

The forbidden cases are:

- run scripts or advanced scripts.
- Client Script behavior or `g_form` logic.
- Business Rule, Script Include, Flow, ACL, or integration creation.
- cross-table behavior.
- data migration or data repair.
- role, ACL, property, credential, or security changes.
- direct mutation of system tables outside the generated UI Policy customer updates.

## Output Schema

The future provider output must be structured implementation intent, not free-form XML:

- `capability`: `ui_policy_generate`.
- `target_table`.
- `policy_name`.
- `condition`.
- `reverse_if_false`.
- `run_scripts`.
- `view`.
- `fields_read`.
- `actions`.
- `test_plan`.
- `rollback_notes`.
- `reviewer_notes`.

Each action must include:

- `field_name`.
- `mandatory`.
- `visible`.
- `read_only`.
- `cleared`.

The builder converts validated structured output into retrieved Update Set XML. The provider must not provide raw `sys_update_xml` as the authoritative artifact.

## Deterministic Validators

The `ui_policy_generate` profile must fail closed unless all deterministic validators pass:

- target table context is retrieved.
- form layout and existing UI Policy context are retrieved.
- referenced condition fields exist on the target table or inherited table.
- referenced action fields exist on the target table or inherited table.
- generated output has `run_scripts=false`.
- generated output has no script fields, client code, endpoints, credentials, secrets, tokens, or API keys.
- generated output contains only `sys_ui_policy` and `sys_ui_policy_action` customer updates.
- generated retrieved Update Set XML can be parsed and references only the intended customer updates.

## UAT Story Shape

A story eligible for future UI Policy generation must name:
This UAT story shape is required before runtime generation can be enabled.

- target table.
- policy name or business name.
- condition.
- reverse-if-false expectation.
- fields read by the condition.
- fields affected by actions.
- whether each affected field should become mandatory, visible, or read-only.
- test data setup.
- observable acceptance criteria.
- rollback expectation.

If any required detail is missing, the story routes to clarification. If forbidden behavior is requested, the story routes to human review or manual developer build.

## Consequences

- Sprint 123 can implement `ui_policy_generate` without inventing the mutation boundary during coding.
- UI Policy generation remains separate from Client Script, Business Rule, Flow Designer, ACL, integration, and data migration generation.
- Flow Designer and Discovery remain context/investigation surfaces until their own generation profiles define graph shape, validators, Update Set evidence, and UAT expectations.
