# Capability-Based Automation Gate Design

## Context

The current UAT behavior exposed an architecture issue. `STRY0010001` asks for a new string field on the Incident form:

- target table: `incident`
- field label: `Antics`
- likely field name: `u_antics`
- field type: `string`
- max length: `4000`
- placement: below `description`
- story points: `2`

The deterministic gate routed the story to `Manual Build` because it did not infer allowlisted `rm_story` tables. That was a product bug in the gate design. The table should not determine whether AI can build. The gate should decide whether the requested change is within the development pipeline's supported capabilities, whether the story is clear enough, and whether the risk/complexity profile is acceptable.

## Product Decision

Replace table-specific automation gating with a capability-based automation gate.

Table names are metadata. They can influence risk, validation, and implementation lookup, but they are not allowlist gates by themselves.

The first baseline pipeline capability is generic dictionary field creation plus form placement for any discoverable table.

## Goals

- Support generic custom field creation on any ServiceNow table the integration identity can inspect and update.
- Support deterministic form placement for a new field on the target table's primary form layout.
- Route suitable low-complexity stories to AI build even when the target is not `rm_story`.
- Give precise feedback when a story is unclear, too complex, or asks for unsupported capabilities.
- Keep retrieved Update Set handoff as the review surface.
- Preserve test-first development and the 90% coverage gate.

## Non-Goals

- Do not implement ACL generation in this sprint.
- Do not implement Flow Designer, Business Rule, Script Include, integration, or data migration capabilities in this sprint.
- Do not bypass retrieved Update Set review.
- Do not use direct permanent Table API mutation as the production fulfillment path.
- Do not hardcode Incident-specific behavior as a shortcut.

## Capability Taxonomy

Stories are classified into one or more requested capabilities:

- `dictionary_field_create`
- `form_layout_place_field`
- `field_label_create`
- `choice_values_create`
- `acl_modify`
- `flow_modify`
- `business_rule_create`
- `script_include_modify`
- `data_migration`
- `integration_modify`
- `unknown`

For this sprint, the supported baseline capabilities are:

- `dictionary_field_create`
- `field_label_create`
- `form_layout_place_field`

`choice_values_create` can be supported later as an extension for choice fields. Until then, choice-field stories may still be classified correctly but should route to a capability gap if values are required.

## Automation Suitability Gate

The suitability gate is target-agnostic. It evaluates whether the story is likely to produce an acceptable automated implementation.

Inputs:

- story points
- short description
- description
- acceptance criteria
- inferred target table
- inferred field label/name/type/length
- requested capabilities
- risk markers
- supported pipeline capabilities
- instance metadata discovery results

Positive signals:

- story points are within policy threshold
- target table is identifiable and exists
- requested field details are explicit or safely derivable
- placement anchor is explicit or there is a safe default
- acceptance criteria are testable
- requested capabilities are supported
- no security/workflow/integration/data migration changes are requested

Negative signals:

- missing target table
- missing field label/type
- ambiguous placement with no safe default
- story points exceed policy
- security, ACL, workflow, integration, script, or data migration requirements
- unsupported capability
- target table or form metadata cannot be discovered
- request implies permissions such as "all users can read/write" without an explicit ACL policy

Outcomes:

- `automated_build`: all required capabilities are supported, story is clear enough, and risk is within threshold.
- `needs_clarification`: story is probably automatable but missing required details.
- `unsupported_capability`: story is clear but asks for a capability the pipeline does not implement yet.
- `manual_developer_build`: story is too complex or risky for automated fulfillment.

## Generic Dictionary/Form Capability

The generic builder should derive an implementation plan from normalized field/form intent:

- `target_table`
- `field_label`
- `field_name`
- `field_type`
- `max_length`
- `mandatory`
- `default_value`
- `placement_anchor`
- `placement_position`

Field name derivation:

- If the story gives a technical name, validate it.
- If only a label is given, derive a custom field name with `u_` prefix.
- Reject or clarify if derivation would be ambiguous or invalid.

Target table discovery:

- Resolve table labels and names through ServiceNow metadata.
- Confirm the target table exists.
- Confirm the table supports custom fields.
- Treat table popularity or operational criticality as risk, not as a hard block.

Form placement:

- Resolve the target table's primary form sections.
- Prefer explicit placement anchors, such as below `description`.
- If no anchor is provided, use a deterministic default section only when the story remains low risk and the acceptance criteria do not require a specific placement.
- Generate retrieved `sys_update_xml` rows for form layout changes.

Validation:

- Generated XML must contain a retrieved Update Set header.
- Customer updates must link through `remote_update_set`.
- No local `sys_update_set` mutation is allowed during handoff.
- After import, the worker links the retrieved Update Set to the story and moves the story to Ready for Testing.

## Feedback Contract

When automation does not proceed, the story work note should explain the reason in product terms:

- what was understood
- what capability was requested
- whether the request is automatable in principle
- what detail or pipeline capability is missing
- what a human developer or product owner must provide next

Example for an unsupported but clear request:

> This story appears automatable, but the current pipeline does not yet support Flow Designer updates. Required capability: `flow_modify`. Provide the flow name, trigger, target action, and expected test evidence, or route to a developer build.

Example for a clarification case:

> This story appears automatable as a dictionary/form change, but the target table could not be identified. Provide the table name or table label, field label, field type, and form placement anchor.

## STRY0010001 Expected Classification

`STRY0010001` should classify as:

- `target_table=incident`
- `field_label=Antics`
- `field_name=u_antics`
- `field_type=string`
- `max_length=4000`
- `placement_anchor=description`
- `placement_position=below`
- capabilities: `dictionary_field_create`, `field_label_create`, `form_layout_place_field`
- suitability: `automated_build`

The acceptance criterion "All incident users are able to read and write to the Antics field" should not cause automatic ACL generation. For this baseline capability, it should be interpreted as a validation expectation under inherited/default field access unless explicit ACL changes are requested. If the instance metadata indicates ACL work is required, the story should route to `unsupported_capability` for `acl_modify`.

## Architecture Changes

Introduce a capability analysis layer before implementation packet generation:

1. Normalize the story into a `StoryCapabilityAssessment`.
2. Use the assessment to decide automation suitability.
3. Build an implementation packet from normalized intent, not table-specific hardcoded assumptions.
4. Generate retrieved Update Set XML through capability builders.
5. Write outcome-specific feedback to ServiceNow.

Recommended modules:

- `capabilities.py`: capability taxonomy, assessment models, and suitability decisions.
- `capability_analysis.py`: deterministic story parsing and metadata-assisted analysis.
- `generic_dictionary_form.py`: generic builder for dictionary field and form placement customer updates.
- `model_fulfillment.py`: orchestration only; no table-specific gate logic.

## Error Handling

- If analysis cannot identify required story details, write `u_ai_status=Needs Clarification` and a clarifying work note.
- If analysis identifies unsupported capabilities, write `u_ai_status=Human Review Required` and list missing capabilities.
- If fulfillment fails after claiming a story, reset to Draft when the active Draft state choice is discoverable and set `u_ai_status=Automation Failed`.
- Never convert an analysis limitation into a generic worker exception after artifacts are persisted.

## Testing Strategy

Tests must be written first.

Required coverage:

- `STRY0010001` classifies as automated dictionary/form work for `incident`.
- `STRY0010013` continues to classify and build successfully for `rm_story`.
- Missing target table routes to `needs_clarification`.
- ACL/workflow/integration/data migration wording routes away from automated dictionary/form fulfillment.
- Unsupported but clear capabilities produce explicit missing-capability feedback.
- Generic builder generates dictionary, documentation, and form layout customer updates without direct local mutation.
- Runtime writes correct ServiceNow feedback for automated, clarification, unsupported, manual, and failed outcomes.

## Rollout Plan

1. Add capability assessment models and tests.
2. Add deterministic analyzer tests for `STRY0010001`, `STRY0010013`, and negative cases.
3. Refactor implementation packet generation to consume capability assessment.
4. Generalize dictionary/form XML generation beyond `rm_story`.
5. Update model fulfillment to route by suitability outcome.
6. Run a live UAT retry for `STRY0010001`.

## Open Risks

- Generic form placement can be more complex on heavily customized forms. The first version should use deterministic section/anchor resolution and fail closed with a clear explanation when ambiguous.
- Table API admin access is powerful. Production posture still requires retrieved Update Set review, audit logs, and no direct apply for generated configuration.
- Some field access behavior depends on ACLs. The baseline capability should not silently create or change ACLs.
