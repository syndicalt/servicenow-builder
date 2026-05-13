# ADR 0002: FedRAMP-Aligned Authorization Boundary First

## Status

Accepted.

## Context

The platform may operate in Federal or contractor environments where model, storage, logging, and network choices are constrained by an authorization boundary. The project cannot assume that a high-capability public model endpoint is permitted.

## Decision

The system will select model providers, embedding providers, vector stores, logs, and artifact storage only through explicit policy. Public commercial AI endpoints are disabled unless an approved Federal authorization path exists for the target data class and task.

## Consequences

- The MVP must work in rules-only/template-only mode.
- Now Assist, Federal cloud-hosted models, private models, and external providers are policy-driven options rather than hard dependencies.
- Provider policy checks happen before prompt construction or data transfer.
- Unauthorized provider access is a testable failure condition.
