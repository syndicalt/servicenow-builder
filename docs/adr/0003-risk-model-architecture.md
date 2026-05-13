# ADR 0003: Risk Model Architecture

## Status

Accepted.

## Decision

Use a **Deterministic risk rubric first** for MVP fulfillment routing. A specialized risk model is deferred until the project has enough reviewer outcome data to evaluate whether a model improves decisions over explicit rules.

## Context

`STRY0010013` showed that the earlier hardcoded risk score of `0.35` was too conservative for a simple optional custom field placed on a form. The story adds `rm_story.u_ai_review_notes` and places it on the Story form. It does not change access controls, workflows, integrations, mandatory behavior, or data migration behavior.

The correct near-term product behavior is to route this class of candidate to automated development fulfillment when confidence is high enough and risk is low enough, while preserving review, audit, and non-production gates.

## Rationale

A specialized risk model would be premature right now because:

- There is no labeled reviewer outcome dataset.
- The first risk categories are easy to express as inspectable rules.
- Regulated environments need explainable routing decisions.
- A learned model would still need a policy gate and deterministic override rules.

The deterministic rubric is also easier to challenge. If a score looks wrong, we can point to the contributing factors instead of reverse-engineering model behavior.

## Current Rubric

Base risk starts at `0.10`.

Risk additions:

- Dictionary/form story: `+0.02`
- Mandatory new field: `+0.15`
- Default value: `+0.05`
- Target table other than `rm_story`: `+0.15`
- Non-custom field name: `+0.10`
- Access control change: `+0.35`
- Workflow change: `+0.25`
- Integration change: `+0.35`
- Data migration: `+0.35`

Scores are capped at `1.0`.

`STRY0010013` scores `0.12`: base `0.10` plus dictionary/form `0.02`.

## Future Model Criteria

Revisit a specialized risk model only after collecting reviewer outcome data such as:

- approved as generated
- approved with edits
- rejected
- routed to manual build
- defect found during test
- unsafe table/operation caught by reviewer
- actual time saved

A future model must be evaluated against the deterministic rubric and must not bypass policy gates.

## Consequences

- Risk scoring is explainable and testable now.
- Early automation remains conservative without being needlessly pessimistic.
- Model work is deferred until there is enough evidence to justify it.
