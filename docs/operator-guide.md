# Operator Guide

The operator documentation for the JEDI DevProject sidecar runtime is split into four focused
guides. For the full runtime architecture, workflow diagrams, and data-flow diagrams, see
`docs/system-architecture.md`.

- `docs/installation.md` — environment configuration, the Docker build-context contract, the
  local container stack, the hosted Railway process split, and the runtime role boundary.
- `docs/local-development.md` — the local verification gate, live smoke testing,
  implementation packet and candidate review, and lifecycle and container smoke runs.
- `docs/runtime-operations.md` — the PostgreSQL operational store, lifecycle webhook and
  artifact retrieval APIs, external alert delivery, the admin console, the fulfillment worker,
  runtime wiring, the ChatGPT implementation adapter, the capability-based automation gate,
  ServiceNow bootstrap commands, and the lifecycle event, build claim, writeback, external
  build pipeline, and artifact handoff contracts.
- `docs/security-hardening.md` — rate limits and payload bounds, the production runtime
  fail-closed checklist, and the secret inventory.

Related references: `docs/development.md` for test strategy, `docs/admin-auth-config.md` for
admin console identity configuration, and `docs/system-architecture.md` for architecture.

## Section Index

| Section | Guide |
|---|---|
| Local Configuration | `docs/installation.md` |
| Container Runtime | `docs/installation.md` |
| Hosted Railway Process Split | `docs/installation.md` |
| Runtime Role Boundary | `docs/installation.md` |
| Verification | `docs/local-development.md` |
| Live Smoke Testing | `docs/local-development.md` |
| Implementation Packet Review | `docs/local-development.md` |
| Lifecycle Smoke | `docs/local-development.md` |
| Container Lifecycle Smoke | `docs/local-development.md` |
| Operational Store | `docs/runtime-operations.md` |
| Lifecycle Webhook API | `docs/runtime-operations.md` |
| Artifact Retrieval API | `docs/runtime-operations.md` |
| External Alert Delivery | `docs/runtime-operations.md` |
| Admin Console | `docs/runtime-operations.md` |
| Fulfillment Worker | `docs/runtime-operations.md` |
| Runtime Wiring | `docs/runtime-operations.md` |
| ChatGPT Implementation Adapter | `docs/runtime-operations.md` |
| Capability-Based Automation Gate | `docs/runtime-operations.md` |
| CI/CD Update Set API Capability | `docs/runtime-operations.md` |
| Update Set XML Importer Bootstrap | `docs/runtime-operations.md` |
| Lifecycle Event Contract | `docs/runtime-operations.md` |
| Build Claim Writeback | `docs/runtime-operations.md` |
| Writeback Planning | `docs/runtime-operations.md` |
| External Build Pipeline Contract | `docs/runtime-operations.md` |
| Artifact Handoff Contract | `docs/runtime-operations.md` |
| Rate Limits and Payload Bounds | `docs/security-hardening.md` |
| Production Runtime Fail-Closed Checklist | `docs/security-hardening.md` |
| Secret Inventory | `docs/security-hardening.md` |
