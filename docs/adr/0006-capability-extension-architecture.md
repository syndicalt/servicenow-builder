# ADR 0006: Capability Extension Architecture

## Status

Accepted.

## Context

The MVP can automate one narrow build class: generic dictionary field creation plus form placement, handed off as a retrieved Update Set for human preview and commit.

The product direction is broader than tables and forms. It must eventually investigate and build across Business Rules, Client Scripts, UI Policies, Flow Designer records, Script Includes, Discovery/CMDB surfaces, integrations, and other ServiceNow configuration. That does not mean the model should be given unconstrained admin access. The system needs a repeatable expansion model where new build surfaces are introduced only after their context, validation, and review boundaries are explicit.

## Decision

Introduce a versioned `CapabilityProfile` contract and a capability registry. A story can enter automated build only when the registry contains an active profile for the requested capability and the runtime can satisfy that profile.

Each `CapabilityProfile` must define:

- Capability id, version, lifecycle status, and owner.
- Supported ServiceNow artifacts and target tables.
- UAT story shape, including required story fields and acceptance criteria signals.
- `required_instance_context`, also described as required context surfaces, that must be retrieved before model execution.
- Model input and output schema for the implementation packet.
- deterministic validators for generated output.
- Unsupported cases and mandatory human-review routes.
- Retrieved Update Set handoff rules and evidence requirements.
- Test fixtures for happy path, clarification, human review, and failed validation.

Runtime selection follows this sequence:

1. Deterministic story analysis proposes a capability and extracts requested artifacts.
2. The investigator retrieves every `required_instance_context` surface named by the profile.
3. The model is called only if the profile is active, context is sufficient, story risk is acceptable, and deterministic validators exist.
4. Generated output is validated before any retrieved Update Set is created.
5. Retrieved Update Set preview/commit remains the human review boundary.

Missing profiles, insufficient context, unsupported cases, failed validators, excessive story points, or ambiguous acceptance criteria route to clarification or human review. The model is never asked to infer unavailable ServiceNow shape.

## Next Capability

Sprint 112 should implement Business Rule analysis first. This is a context-only first implementation that retrieves and classifies current `sys_script` state, identifies whether a story appears to need Business Rule generation, and reports missing inputs or unsupported cases without creating a new Business Rule.

Business Rule generation is the next build candidate after that analysis profile is proven. It is the right next mutation candidate because Business Rules are represented by deterministic ServiceNow records, can be reviewed inside a retrieved Update Set, and can be scoped more tightly than Flow Designer.

The first Business Rule generation profile should support only table-local before/after insert/update rules with explicit conditions and simple field updates or comments. It must not support delete rules, scheduled jobs, embedded credentials, outbound REST calls, broad GlideRecord updates, ACL changes, Script Include creation, or cross-table data migrations.

Flow Designer remains context-only until a separate profile defines flow graph retrieval, model output shape, validators, and update set evidence. Flow records are too graph-oriented to treat as a small variant of dictionary/form or Business Rule generation.

## UAT Story Shape

Business Rule analysis and future generation stories must name:

- Target table.
- Trigger timing: before or after.
- Trigger operations: insert and/or update.
- Condition in business terms.
- Expected action in business terms.
- Fields that may be read or written.
- Acceptance criteria with observable ServiceNow behavior.
- Test record setup and expected evidence.
- Explicit exclusions for integrations, ACLs, scheduled jobs, and cross-table updates.

## Consequences

- Capability growth is slower, but every new mutation class has an explicit safety case.
- Generic surface investigation can continue independently of build support.
- The capability registry prevents one-off generators from becoming hidden production behavior.
- Human review remains native to ServiceNow through retrieved Update Set preview and commit.
