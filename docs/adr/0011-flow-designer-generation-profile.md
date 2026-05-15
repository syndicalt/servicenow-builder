# ADR 0011: Flow Designer Generation Profile

## Status

Accepted.

## Context

Flow Designer is a graph-oriented ServiceNow surface. A flow is not one record; it can involve `sys_hub_flow`, trigger records such as `sys_hub_trigger_instance`, action records such as `sys_hub_action_instance`, logic records such as `sys_hub_flow_logic_instance_v2`, snapshots, inputs, outputs, and runtime records. Treating Flow Designer as a small variant of Business Rule or UI Policy generation would create hidden graph corruption risk.

The product should eventually handle low-complexity Flow Designer stories, but only after the app can retrieve a complete flow graph, produce a structured graph diff, validate the diff, and hand the resulting customer updates to ServiceNow for native preview/commit.

## Decision

Define the future `flow_modify` capability profile. No runtime generation is enabled by this ADR.

Sprint 125 adds read-only `flow_graph` retrieval as prerequisite context. This is not a builder and does not mutate Flow Designer records. The context worker retrieves current graph shape from approved ServiceNow metadata tables and fails closed when a required graph cannot be assembled.

Sprint 126 adds a validation-only `sys_hub_flow_graph_diff` contract. This contract lets the system validate a future provider's structured graph diff before any retrieved Update Set builder exists. It does not route Flow Designer output into handoff.

Sprint 127 adds Flow Designer builder preflight planning. The preflight verifies `retrieved_graph_hash_matches_existing_graph_hash` and emits the builder evidence still required before customer updates can be produced. The current blocked reason is `Flow Designer builder is design-only`; runtime generation remains disabled.

Sprint 128 adds the Flow XML shape repository `flow-xml-shapes-v1`. The repository documents approved customer-update shapes for `sys_hub_flow`, `sys_hub_action_instance`, and `sys_hub_flow_logic_instance_v2`. These shapes are review metadata only; there is still no Flow XML builder and no retrieved Update Set handoff.

Sprint 129 adds the Flow XML shape evidence validator `validate_flow_xml_shape_evidence`. The validator parses retrieved review samples and verifies the expected `record_update` root, `INSERT_OR_UPDATE` action, required fields, and forbidden field absence against `flow-xml-shapes-v1`. This is still no Flow XML builder and no retrieved Update Set handoff; it only proves whether collected XML evidence matches the repository contract.

Sprint 130 adds the Flow customer update strategy `flow-customer-update-strategy-v1`. The strategy defines the `table_sys_id` customer update naming convention for approved Flow tables and names rollback strategy coverage for the narrow `add_action` and `update_condition` diff operations. This is still no Flow XML builder and no retrieved Update Set handoff; it only proves that customer update names and rollback strategy are explicit before builder work starts.

Sprint 131 adds the Flow snapshot update strategy `flow-snapshot-update-strategy-v1`. The strategy requires retrieved `latest_snapshot` evidence on `sys_hub_flow`, rejects unstable snapshot references, and makes clear that snapshot table mutation is not supported in the current Flow path. This is still no Flow XML builder and no retrieved Update Set handoff; it only defines the snapshot evidence boundary for future builder work.

Sprint 132 adds the Flow preview/commit review strategy `flow-preview-commit-review-strategy-v1`. The strategy names the review boundary as `retrieved_update_set_preview_commit`, requires preview before commit, requires human commit, and states that auto-commit is not supported for Flow Designer. This is still no Flow XML builder and no retrieved Update Set handoff; it only makes the ServiceNow human review boundary machine-checkable.

Sprint 133 adds the Flow builder readiness contract `flow-builder-readiness-v1`. The contract aggregates the required graph, XML shape, customer update naming, snapshot, rollback, and preview/commit evidence into one auditable readiness object with `missing_evidence`. The contract still reports `Flow Designer builder is not implemented`; it is not permission to generate XML.

Sprint 134 adds Flow builder plan readiness wiring. The builder preflight plan now carries `readiness_contract_version`, `missing_builder_evidence`, `ready_for_runtime_generation=false`, `ready_for_retrieved_update_set_handoff=false`, and the readiness blocked reason. This is still no Flow XML builder and no retrieved Update Set handoff; it only makes readiness unavoidable for preflight consumers.

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

The validation-only pseudo-table is `sys_hub_flow_graph_diff`. Its currently allowed operations are:

- `add_action`.
- `update_condition`.

The builder converts validated structured graph output into retrieved Update Set XML. The provider must not provide raw `sys_update_xml` as the authoritative artifact.

The builder preflight requires these evidence items before implementation can move beyond design:

- `xml_shape_repository_available`.
- `xml_shape_evidence_validator_available`.
- `customer_update_name_strategy_defined`.
- `flow_snapshot_update_strategy_defined`.
- `rollback_customer_update_strategy_defined`.
- `servicenow_preview_commit_review_required`.

The Flow XML shape repository records:

- root element `record_update`.
- record element for each target table.
- `INSERT_OR_UPDATE` as the only allowed action.
- required fields needed before a customer update can be emitted.
- forbidden fields that should not be generated.
- review notes explaining shape-specific risks.

The Flow XML shape evidence validator records:

- repository version used for validation.
- target table and record element.
- required fields present in the review sample.
- fail-closed errors for missing required fields.
- fail-closed errors for forbidden fields.
- `runtime_generation_enabled=false`.
- `retrieved_update_set_handoff_enabled=false`.

The Flow customer update strategy records:

- strategy version `flow-customer-update-strategy-v1`.
- naming pattern `table_sys_id`.
- approved Flow tables from `flow-xml-shapes-v1`.
- rollback strategy text for `add_action`.
- rollback strategy text for `update_condition`.
- `runtime_generation_enabled=false`.
- `retrieved_update_set_handoff_enabled=false`.

The Flow snapshot update strategy records:

- strategy version `flow-snapshot-update-strategy-v1`.
- Flow record table `sys_hub_flow`.
- snapshot reference field `latest_snapshot`.
- required retrieved snapshot evidence.
- unsupported snapshot and version tables.
- fail-closed validation when snapshot table mutation is requested.
- `runtime_generation_enabled=false`.
- `retrieved_update_set_handoff_enabled=false`.

The Flow preview/commit review strategy records:

- strategy version `flow-preview-commit-review-strategy-v1`.
- review boundary `retrieved_update_set_preview_commit`.
- preview required before commit.
- human commit required.
- auto-commit disabled.
- fail-closed validation when auto-commit is requested.
- `runtime_generation_enabled=false`.
- `retrieved_update_set_handoff_enabled=false`.

The Flow builder readiness contract records:

- contract version `flow-builder-readiness-v1`.
- all required builder evidence.
- `missing_evidence` for incomplete preflight inputs.
- `ready_for_runtime_generation=false`.
- `ready_for_retrieved_update_set_handoff=false`.
- blocked reason `Flow Designer builder is not implemented`.

Flow builder plan readiness wiring records:

- `readiness_contract_version` on each builder plan.
- `missing_builder_evidence` on each builder plan.
- `ready_for_runtime_generation=false`.
- `ready_for_retrieved_update_set_handoff=false`.
- readiness blocked reason on each builder plan.

## Deterministic Validators

The `flow_modify` profile must fail closed unless all deterministic validators pass:

- target flow context is retrieved.
- `flow_graph` context is retrieved from approved `sys_hub_*` records.
- flow graph retrieval includes read-only citations for `sys_hub_trigger_instance`, `sys_hub_action_instance`, `sys_hub_flow_logic_instance_v2`, `sys_hub_trigger_input`, `sys_hub_trigger_output`, `sys_hub_action_input`, and `sys_hub_action_output`.
- runtime execution history records are excluded from mutation.
- graph diff references only retrieved nodes and edges.
- graph diff validation rejects any unretrieved node reference.
- graph diff validation rejects raw XML and raw `sys_update_xml`.
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
