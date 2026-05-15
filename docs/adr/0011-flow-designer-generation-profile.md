# ADR 0011: Flow Designer Generation Profile

## Status

Accepted.

## Context

Flow Designer is a graph-oriented ServiceNow surface. A flow is not one record; it can involve `sys_hub_flow`, trigger records such as `sys_hub_trigger_instance`, action records such as `sys_hub_action_instance`, logic records such as `sys_hub_flow_logic_instance_v2`, snapshots, inputs, outputs, and runtime records. Treating Flow Designer as a small variant of Business Rule or UI Policy generation would create hidden graph corruption risk.

The product should eventually handle low-complexity Flow Designer stories, but only after the app can retrieve a complete flow graph, produce a structured graph diff, validate the diff, and hand the resulting customer updates to ServiceNow for native preview/commit.

## Decision

Define the future `flow_modify` capability profile. No runtime generation is enabled by this ADR.

The first supported subset should be limited to:

- modifying one active flow at a time.
- record-triggered flows only.
- one target table or one explicit trigger context.
- one additive action or one narrow condition change.
- no custom action creation.
- no spokes, credentials, REST steps, or integration steps.
- no subflow orchestration.
- no approval orchestration.
- no scripts.
- generated changes must be represented as reviewed customer updates inside `sys_update_xml`.
- Retrieved Update Set preview/commit remains the human review boundary.

The forbidden cases are:

- graph rewrites.
- custom actions.
- spokes and integrations.
- credentials, secrets, tokens, API keys, usernames, or passwords.
- subflows.
- approval orchestration.
- script steps.
- data migration or data repair.
- changes to runtime execution history tables.
- direct mutation of Flow runtime state outside reviewed customer updates.

## Output Schema

The future provider output must be a structured graph diff, not raw XML:

- `capability`: `flow_modify`.
- `flow_name`.
- `flow_sys_id_or_stable_key`.
- `target_table`.
- `trigger_summary`.
- `existing_graph_hash`.
- `requested_graph_diff`.
- `affected_nodes`.
- `affected_edges`.
- `customer_update_records`.
- `test_plan`.
- `rollback_notes`.
- `reviewer_notes`.

The builder converts validated structured graph output into retrieved Update Set XML. The provider must not provide raw `sys_update_xml` as the authoritative artifact.

## Deterministic Validators

The `flow_modify` profile must fail closed unless all deterministic validators pass:

- target flow context is retrieved.
- flow graph context is retrieved from approved `sys_hub_*` records.
- runtime execution history records are excluded from mutation.
- graph diff references only retrieved nodes and edges.
- generated diff is additive or narrowly edits an allowed condition.
- generated output has no custom action, credential, script, REST, SOAP, spoke, subflow, or approval orchestration changes.
- generated customer updates reference only intended Flow Designer records.
- generated retrieved Update Set XML can be parsed and references only the intended customer updates.

## UAT Story Shape

A story eligible for future Flow Designer generation must name this UAT story shape:

- flow name.
- target table or trigger.
- trigger condition.
- existing graph behavior in business terms.
- requested action or condition change.
- expected record behavior.
- test data setup.
- observable acceptance criteria.
- rollback expectation.

If any required detail is missing, the story routes to clarification. If forbidden behavior is requested, the story routes to human review or manual developer build.

## Consequences

- Sprint 125 should harden flow graph retrieval before implementation is considered.
- Flow Designer generation remains disabled until graph retrieval, graph diff validation, and Update Set XML evidence are implemented.
- Flow Designer should not be emulated through Business Rules or Client Scripts to bypass this profile.
