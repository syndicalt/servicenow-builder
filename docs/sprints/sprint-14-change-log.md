# Sprint 14 Change Log

## SPM/PPM workflow research

- Reviewed official ServiceNow Strategic Portfolio Management, Demand Management, and Agile Development 2.0 documentation.
- Confirmed that Demand Management owns upstream intake, assessment, approval, and conversion into downstream artifacts.
- Confirmed that Agile Development 2.0 owns story execution through backlog, sprint, release, and dashboard workflows.
- Confirmed that Agile 2.0 reporting tracks Ready, Work in Progress, Ready for Testing, Testing, and Complete story flow.

## Architecture Decision

- Added ADR 0004 to make ServiceNow the canonical ServiceNow work surface.
- Defined this product as an SPM-aware sidecar rather than a competing workflow UI.
- Scoped the external build pipeline outside the project lifecycle while preserving ServiceNow writeback.
- Set Ready for Testing as the first automated story state advancement after external build completion and policy checks.

## Structured Writeback

- Documented that comments/work notes are acceptable for human-readable summaries but not sufficient as the product integration protocol.
- Required structured writeback for status, risk, confidence, artifact references, fulfillment route, and build completion evidence.
- Required state write allowlists and instance-specific state discovery before automated state transitions.
