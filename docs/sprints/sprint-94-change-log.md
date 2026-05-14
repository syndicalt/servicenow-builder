# Sprint 94 Change Log

## Goal

Start the confidence-driven context escalation path without adding agentic complexity or letting model self-confidence drive automation decisions.

## Changes

- Added deterministic `context_sufficiency` metadata to implementation packets.
- Marked packets without live instance discovery as `needs_retrieval` with missing context `live_instance_context`.
- Marked discovered table/form context as `sufficient` when the target table exists, supports custom fields, and includes form sections.
- Included `context_sufficiency` in the model payload controls so downstream workers and providers can see whether the packet was grounded in current instance state.

## Tests

- Added packet coverage for missing instance context requiring retrieval.
- Added packet coverage proving discovered Incident form context is scored as sufficient.

## Decision

Context confidence must be computed from deterministic evidence, not from the LLM's subjective confidence. The next escalation step should use this packet metadata to decide when to run an additional ServiceNow context retrieval worker before model generation or Update Set handoff.
