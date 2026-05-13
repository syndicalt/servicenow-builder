# ADR 0004: SPM-Aware Sidecar Work Surface

## Status

Accepted.

## Context

The product must fit standard ServiceNow Strategic Portfolio Management (SPM), Project Portfolio Management (PPM), Demand Management, and Agile Development workflows rather than replacing them.

ServiceNow SPM is intended to align work with strategy and plan, deliver, and track value across methodologies. Demand Management provides the upstream intake and assessment path, including Draft, Submitted, Screening, Qualified, Deferred, Approved, and Completed demand states. Approved demands can create downstream artifacts including projects, changes, enhancements, defects, Agile Development entities, SAFe entities, and Enterprise Agile Planning entities depending on installed applications and demand category/type.

Agile Development 2.0 provides the delivery workflow after work has entered an agile execution path. Its common process includes products, epics, stories, releases, personalized backlogs, assignment groups, sprints, sprint planning, sprint tracking, and release tracking. ServiceNow's Agile 2.0 release dashboard explicitly tracks story flow through Ready, Work in Progress, Ready for Testing, Testing, and Complete.

The build process for generated implementation work will happen outside the project scope of this MVP. The product still needs to coordinate with the native ServiceNow workflow so that users can see when external build output is ready for validation.

References:

- ServiceNow Strategic Portfolio Management overview: https://www.servicenow.com/docs/r/fr-FR/it-business-management/r_ITBusinessManagement.html
- ServiceNow Demand workflow: https://www.servicenow.com/docs/r/it-business-management/strategic-planning/demand-process-flow.html
- ServiceNow Create an artifact from a demand: https://www.servicenow.com/docs/r/it-business-management/demand-management/t_CrtArtftDmdMnu.html
- ServiceNow Agile Development process flow: https://www.servicenow.com/docs/r/it-business-management/agile-development/agile-development-process-flow.html
- ServiceNow Agile 2.0 Release Dashboard: https://www.servicenow.com/docs/r/it-business-management/agile-development/agile-development-release-dashboard.html

## Decision

ServiceNow remains the canonical work surface and workflow system of record.

This product will run as an SPM-aware sidecar automation service. It will monitor approved ServiceNow work records, generate reviewable candidate artifacts, coordinate with the external build pipeline, and write structured status back to ServiceNow. It will not replace Demand Management, Project Management, Agile Development 2.0, sprint planning, release tracking, project governance, or human approval.

For agile stories, the sidecar may write back only at defined control points:

- Story moves from Draft to Ready: ServiceNow emits a lifecycle event to the sidecar to start evaluation. This event is the trigger for orchestration; comments and work notes are not command inputs.
- Candidate generated: record analysis status, confidence, risk, artifact reference, assumptions, and reviewer notes.
- Candidate referred to external build pipeline: record fulfillment route and pipeline handoff metadata.
- Candidate accepted for automated fulfillment: claim the story by setting it to Work in Progress after fresh story verification and allowlisted transition checks.
- External build complete: record build output reference and set the story to Ready for Testing when policy permits the state transition.
- External build failed or blocked: record the failure reason and route the story to human review without advancing the story state.

Comments or work notes may be used for human-readable summaries, but they are not the primary integration protocol. Machine state must use structured fields, related records, attachments, or artifact links so the workflow can be queried, audited, and tested.

## Consequences

- Users stay in ServiceNow for demand intake, project governance, backlog refinement, sprint execution, testing, and release visibility.
- The sidecar must understand enough SPM/PPM context to avoid moving work at the wrong lifecycle stage.
- Draft to Ready is the first event-driven automation trigger. The event starts evaluation, but build execution still depends on deterministic eligibility, risk, policy, and approval gates.
- The product needs a ServiceNow writeback layer, but writes must be allowlisted by table, field, state, and lifecycle condition.
- Work in Progress is the first permitted automated claim state, and only after a valid ServiceNow lifecycle event plus fresh story verification. Ready for Testing remains the completion state after an external build completion signal plus policy checks.
- The MVP should not create a separate business workflow UI. A future UI may exist for operators to inspect runs, providers, artifacts, and failures.
- Any customer-specific state customizations must be discovered from the instance before state writes are enabled.
