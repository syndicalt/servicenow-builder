# Catalog Item Employee Center Automation Design

## Goal

Add a constrained, production-shaped automation capability for standard ServiceNow Catalog Items that can be reviewed through retrieved Update Sets and surfaced in Employee Center through an existing topic.

## Current Status (2026-06-11)

`catalog_item_create` currently runs in candidate-generation mode only. The Sprint 161 builder-maturity routing model scores the catalog surfaces (`catalog_definitions`, `catalog_categories`, `employee_center_topics`, `employee_center_connected_content`) at 0.60, below `AUTOMATED_HANDOFF_BUILDER_MATURITY_THRESHOLD = 0.75` in `src/jedi_devproject/implementation_packet.py` (`_builder_maturity_for_surface()`), so catalog candidates route to manual review and no retrieved Update Set handoff is created automatically. The Handoff Contract below describes the implemented builder and re-applies when catalog builder maturity crosses the threshold.

**Sprint 163 update.** The builder now additionally supports:

- declarative reference qualifier serialization for reference variables (encoded-query grammar, fail-closed validation, script indicators rejected);
- attachment of EXISTING variable sets via `io_set_item` link updates (variable set creation remains refused);
- container grouping of the item's own variables via `container_start`/`container_end` variables (type ids 19/20);
- sibling catalog behavior capabilities `catalog_ui_policy_generate` (`catalog_ui_policy` / `catalog_ui_policy_action`) and `catalog_client_script_generate` (`catalog_script_client`, deterministic g_form-only rendered scripts), candidate generation only at maturity baseline 0.30 with UAT-unconfirmed XML shape assumptions;
- attachment of an EXISTING active record-triggered fulfillment flow via `sc_cat_item.flow_designer_flow`, resolved fail-closed with reason codes `fulfillment_flow:not_found` / `ambiguous` / `inactive` / `not_record_triggered` (flow creation and modification remain forbidden; new maturity surface `catalog_fulfillment_flows` at 0.30 routes attaching candidates to manual review).

The "Variable Sets and multi-row variable sets" entry in Explicit Non-Scope below is therefore partially superseded: attaching existing variable sets is supported as of Sprint 163, while creating variable sets (including multi-row variable sets) is still refused. The "Fulfillment flow or workflow creation" entry is likewise narrowed: attaching an existing flow is supported; creating or modifying flows is still refused.

## Decision

Implement a first-class `catalog_item_create` capability. Do not fold catalog work into dictionary/form generation.

Catalog items are multi-surface configuration. A complete first-pass build must treat the catalog item, variables, catalog/category placement, and Employee Center topic association as one validated intent with several generated customer updates.

## Supported First Scope

- Create one standard Catalog Item on `sc_cat_item`.
- Create simple catalog variables on `item_option_new`.
- Place the item in one existing catalog and one existing category.
- Associate the item to one existing Employee Center topic through connected content.
- Resolve catalog, category, taxonomy, topic, and content type from live instance context.
- Generate a retrieved Update Set handoff only. Human preview, scan, and commit remain in ServiceNow.

Supported variable types for the first implementation:

- `single_line_text`
- `multi_line_text`
- `checkbox`
- `yes_no`
- `date`
- `reference`

## Explicit Non-Scope

- Record Producers.
- Catalog Client Scripts.
- Catalog UI Policies.
- Variable Sets and multi-row variable sets.
- Fulfillment flow or workflow creation.
- Approval design.
- User criteria or entitlement changes.
- Pricing, images, attachments, order guides, and bundles.
- Creating Employee Center topics or taxonomies.
- Associating to an ambiguous topic/category by guessing.

## Story Shape

Structured stories must provide:

- `Target artifact type: Catalog Item`
- `Artifact name`
- `Short description`
- `Catalog`
- `Category`
- `Taxonomy`
- `Employee Center topic`
- `Variables`

`Variables` uses a compact deterministic format:

```text
Variables: requested_for|Requested for|reference|sys_user|active=true|mandatory=true|order=100; business_justification|Business justification|multi_line_text|mandatory=true|order=200
```

Each variable entry uses:

```text
name|label|type|optional reference table|optional reference qualifier|mandatory=true|order=100|help=Plain help text
```

The parser rejects missing variable name, label, type, reference table for reference variables, unsupported variable type, duplicate variable names, and ambiguous target records.

## Discovery Contract

Catalog item builds require these live surfaces before model generation:

- `catalog_definitions`: active `sc_catalog` records.
- `catalog_categories`: active `sc_category` records and their catalog references.
- `employee_center_topics`: active `topic` records and their taxonomy references.
- `employee_center_connected_content`: active `taxonomy_content_configuration` records, especially `Catalog Item`.

The worker must fail closed if:

- the catalog display name resolves to zero or multiple records;
- the category does not resolve under the selected catalog;
- the taxonomy or topic does not resolve;
- the topic is not under the selected taxonomy;
- the Catalog Item content type is missing.

## Handoff Contract

The retrieved Update Set may include customer updates for:

- `sc_cat_item`
- `item_option_new`
- `sc_cat_item_category`
- `m2m_connected_content`

The generated XML must use deterministic sys_ids for newly created records so variables and relationships can reference the new catalog item inside the same update set. Existing catalog/category/topic/content-type records must come from discovery evidence, not from model invention.

## Safety

The deterministic gate remains the final authority. The model may propose field values, but the builder validates the normalized candidate before XML generation.

Forbidden behavior routes to manual review:

- fulfillment flow/workflow mutation;
- scripts of any kind;
- user criteria or role changes;
- integration calls;
- data migration;
- ACL changes;
- creating taxonomy/topic records.

## Testing

Tests must cover:

- capability registry metadata;
- structured intent extraction;
- capability analysis and missing-detail feedback;
- catalog surface discovery;
- update set customer update generation;
- rejection for unsupported variable types and ambiguous/missing live records;
- model fulfillment path to retrieved Update Set handoff.

Coverage must remain above 90%.
