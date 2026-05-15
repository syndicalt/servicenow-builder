# Sprint 106 Change Log

## Goal

Add a general ServiceNow surface investigation layer before model generation so the worker can retrieve relevant instance context beyond tables and forms, and fail closed when required context is missing.

## Changes

- Added `ServiceNowSurfaceContextBundle` models for broad platform context.
- Added read-only ServiceNow Table API retrieval for:
  - table schema
  - form layout
  - Business Rules
  - Client Scripts
  - UI Policies
  - Flow Designer records
  - Script Includes
  - CMDB/discovery indicators
  - outbound REST integration surfaces
  - public documentation queries through the approved RAG boundary
- Added `instance_context_bundle` to implementation packets and model payloads.
- Added an `instance_context_bundle` DB-backed artifact before the implementation packet and candidate artifacts.
- Added a context gate so provider calls are skipped when required surface context is insufficient.

## Tests

- Added surface discovery coverage for related ServiceNow platform surfaces.
- Added packet coverage for context bundle inclusion and insufficient context escalation.
- Added runtime fulfillment coverage proving:
  - context bundles are emitted as artifacts.
  - missing required Flow context blocks provider invocation.
- Added documentation coverage for the broad surface investigation posture.

## Decision

The investigation layer is broader than the current implementation capability. The current automated build capability remains generic dictionary field plus form placement, but the worker can inspect related ServiceNow surfaces and explain why a story needs human review rather than letting the model infer Flow, Business Rule, Client Script, Discovery, or integration state.

Public documentation retrieval remains behind the curated RAG boundary. The worker does not perform live public internet calls because regulated deployments need explicit egress, provenance, retention, and approval controls before that behavior is safe.
