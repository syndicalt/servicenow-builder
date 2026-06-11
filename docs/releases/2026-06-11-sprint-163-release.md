# Release Announcement — Sprint 163

**Product**: JEDI DevProject — AI-Assisted ServiceNow Delivery Sidecar
**Release date**: June 11, 2026
**Release type**: Capability expansion (minor release)
**Audience**: Delivery leadership, program managers, ServiceNow platform owners, compliance stakeholders

---

## Executive Summary

This release is the largest capability expansion since the platform's MVP. It extends AI-assisted build automation from simple form and field changes into the two highest-demand areas of ServiceNow delivery — **Service Catalog** and **Flow Designer** — while preserving the platform's core guarantee: **no change reaches a ServiceNow instance without named human review and approval.**

Three themes define the release:

1. **Catalog requests can now be automated end to end.** The system can generate complete, reviewable catalog items — including filtered reference fields, grouped variables, shared variable sets, form behavior rules, client-side scripts, and fulfillment-flow attachment — plus record producers as a new request type. These cover the most common categories of catalog work that delivery teams handle today.
2. **Flow Designer automation has moved from design to working machinery.** The deterministic builder, evidence collector, and verification harness specified across fifteen design sprints are now implemented. Flow changes remain disabled in production until per-instance evidence is collected — by design, not by limitation.
3. **The quality loop is closing.** Every generated change can now ship with a proposed automated test plan, rejected requests get actionable rewrite guidance at intake, and a second AI provider option reduces vendor concentration risk.

All work passed the platform's full engineering gate: 1,278 automated tests, 93.6% code coverage (gate: 90%), strict type checking, and zero lint findings.

---

## What's New

### 1. Full Catalog Item Build Automation

**Business value: the most frequently requested story type — "build us a catalog item" — can now be drafted by the system in minutes instead of hours, with every element a reviewer expects already in place.**

| Capability | What it means for requesters |
|---|---|
| Filtered reference fields | "Assignment group, limited to active groups" now generates correctly filtered choices — with strict validation that blocks any script-like filter from entering the platform |
| Variable grouping | Variables can be organized under titled sections instead of one flat list, matching how customers expect forms to read |
| Shared variable sets | Existing, governed variable sets can be attached to new items — reuse over duplication |
| Form behavior rules | "Show the date field only when expedited is Yes" generates the corresponding catalog UI policy |
| Client-side behavior | On-load defaults and on-change interactions generate as locked-down scripts that can only use the platform's sanctioned form API — no free-form code |
| Fulfillment flow attachment | A new item can be wired to an **existing, approved** fulfillment flow at creation time |
| Record producers | A new request type: forms that create records directly (e.g., "report a facilities issue" creating an incident), with field mapping and no custom scripting |

**Safety posture:** All new catalog surfaces launch in **candidate-generation mode** — the system drafts the complete change package, but a developer reviews and applies it. Promotion to automated handoff is earned through recorded user-acceptance results, not configuration. Requests outside the supported envelope (creating new variable sets, custom producer scripts, modifying existing items) are routed to a developer with a clear, specific reason.

### 2. Flow Designer Automation — Machinery Complete, Evidence-Gated

**Business value: the foundation for automating workflow changes — historically the most manual, highest-skill area of ServiceNow configuration — is now built and testable.**

Delivered in this release:

- **Evidence collector** — gathers and validates the exact XML record shapes a target instance uses for flows, with audit hashes and automatic redaction of script content.
- **Deterministic builder** — converts an approved, narrowly-scoped change request (add one action to a flow, or adjust one condition) into platform-native update records. It cannot produce anything outside that envelope.
- **Round-trip verification harness** — imports a generated change into a development instance, re-reads the flow, and proves the result matches the intent exactly. It never commits the change; that remains a human decision in ServiceNow.
- **Evidence-driven readiness** — flow automation now reports precisely which evidence requirements are satisfied and which are outstanding, replacing a hard "off" switch.

**What this means practically:** flow change generation remains **off** in production until the evidence collector is run against the customer's development instance and the round-trip harness passes. The first live evidence-collection run is the next milestone, and it is an operational task, not an engineering one.

### 3. Quality, Feedback, and Resilience

- **Automated test plans with every change.** Generated changes now include a proposed ServiceNow ATF (Automated Test Framework) test plan — open the form, set the values, verify the behavior — derived directly from what was built. Reviewers get a ready-made verification script; passing results feed the maturity model that governs automation privileges.
- **Faster feedback for requesters.** Stories that can't be automated as written now receive specific guidance and a suggested rewrite **at intake** — before a developer ever picks them up. Requesters learn what's missing (a field name, a table, acceptance criteria) while the story is still on their desk. Expected outcome: a higher share of stories pass automation gates on first submission.
- **Second AI provider option.** An Anthropic (Claude) adapter now stands alongside the existing OpenAI integration, with identical safety validation and structured-output contracts. Activating it for any environment remains a governance decision under the existing provider-policy registry — no provider is used without explicit boundary approval. This removes a single-vendor dependency from the platform's risk profile.

---

## Compliance & Safety Posture (Unchanged Guarantees)

This release adds capability without relaxing any control:

- **Human approval boundary intact.** Every generated change is reviewed in ServiceNow's native Retrieved Update Set preview/commit workflow before it touches an instance. Nothing in this release commits automatically.
- **Deterministic generation.** AI models propose intent; locked-down deterministic builders produce the actual platform records. Raw model output is never imported.
- **Fail-closed everywhere.** Missing records, ambiguous names, inactive flows, script-like input, unsupported scope — all route to a developer with a stable, auditable reason code.
- **Earned autonomy.** New capabilities start below the automated-handoff threshold and are promoted only by recorded acceptance evidence — and can be demoted by field failures.
- **Full auditability.** Every artifact carries content hashes, provider/model identity, and citations; sensitive script bodies are redacted before storage.

---

## Known Limitations & Next Steps

| Item | Status |
|---|---|
| New-flow creation from templates | Not in this release — intentionally gated until the flow modify path is proven against a live instance (the platform's evidence-first rule) |
| Flow change generation in production | Dark until evidence collection + round-trip verification run on the target development instance (next operational milestone) |
| Catalog behavior rules / client scripts / record producers / flow attachment | Candidate-generation only; automated handoff requires accumulated UAT evidence |
| Anthropic provider | Implemented and tested; activation requires boundary/policy approval per environment |
| Modifying *existing* catalog items | Out of scope; routed to developers |

**Recommended next actions for stakeholders:**

1. Schedule the flow evidence-collection and round-trip run against the development instance (unlocks the Flow Designer milestone).
2. Begin routing catalog-item stories through the system to accumulate the UAT evidence that promotes the new surfaces toward automated handoff.
3. Initiate provider-policy review if a second AI provider is desired for the target authorization boundary.

---

## Quality Statement

| Metric | Value |
|---|---|
| Automated tests | 1,278 passing (up from 1,030 at sprint start) |
| Code coverage | 93.6% (mandatory gate: 90%) |
| Type safety | Strict static typing, zero findings across 156 modules |
| Lint/style | Zero findings |
| New capabilities launched in candidate-only mode | 5 of 5 |
| Changes that can bypass human review | 0 |

For the engineering-level record of this release, see `docs/sprints/sprint-163-change-log.md`. For per-item roadmap status, see `docs/codebase-analysis-and-roadmap-2026-06-11.md` §4.
