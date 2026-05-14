# Sprint Plan

This plan assumes two-week sprints with a strict test-first workflow, 90% coverage gate, no hacks, and explicit assumption challenges. Each sprint must end with working, reviewed, tested software or a documented decision to reduce scope.

## Sprint 0: Engineering Baseline and Governance

**Goal**: Establish the project skeleton, quality gates, and compliance guardrails before feature work starts.

**Deliverables**
- Python package structure with `src/` and `tests/`.
- `pytest`, coverage reporting, formatting, linting, and type checking.
- CI-equivalent local commands documented.
- Coverage gate set to 90%.
- Initial architecture decision records for no-hacks policy, test-first workflow, and FedRAMP-aligned boundary assumptions.
- Sample regulated-data handling policy for local development.

**Tests First**
- Failing test for package import and CLI smoke behavior.
- Failing test proving coverage threshold enforcement command exists.
- Failing tests for config loading rejecting missing required settings.

**Assumptions to Challenge**
- Python CLI is the fastest credible MVP path.
- Local JSON is acceptable for MVP artifacts.
- 90% line coverage is sufficient only when paired with behavior-focused tests.

**Exit Criteria**
- Fresh checkout can run one documented command to execute tests, coverage, lint, and type checks.
- No production module exists without tests.

## Sprint 1: Core Schemas and Policy Registry

**Goal**: Build typed, validated foundations for stories, project context, provider policy, retrieval citations, and Update Set candidates.

**Deliverables**
- Pydantic models for `Story`, `ProjectContext`, `ProviderPolicy`, `RetrievalCitation`, `UpdateSetCandidate`, and run manifests.
- Validation rules for required story fields, data classification, provider status, and candidate status transitions.
- Artifact hashing utility for auditability.

**Tests First**
- Schema accepts valid minimal story input.
- Schema rejects missing `sys_id`, missing story number, unknown data classification, and invalid candidate status.
- Provider policy rejects calls when task or data class is not allowed.
- Artifact hash is stable for equivalent normalized content.

**Assumptions to Challenge**
- The README field list is sufficient for MVP ingestion.
- Pydantic is the right validation layer rather than dataclasses plus manual validation.
- Provider authorization can be modeled as static policy before live integration.

**Exit Criteria**
- Core schemas are covered above 90%.
- Invalid regulated inputs fail closed.

## Sprint 2: Rules-First Story Classification and Safety Gates

**Goal**: Determine whether a story is eligible, manual-review, or rejected without requiring a model call.

**Deliverables**
- Deterministic story classifier.
- Customer-configurable story type, table, operation, and rejection allowlists.
- Safety gate engine for low-risk criteria.
- Structured eligibility reasons.

**Tests First**
- Label/help-text stories classify as eligible when all allowlists pass.
- ACL, role, integration, migration, credential, destructive delete, and ambiguous stories reject.
- Stories over 3 points route to manual review or rejection per configured policy.
- Missing acceptance criteria routes to manual review.

**Assumptions to Challenge**
- Story points are a weak safety proxy and must never be the only eligibility gate.
- Initial allowlists should be narrow, even if that lowers automation rate.

**Exit Criteria**
- Classifier works on mock backlog data.
- Every decision includes machine-readable reasons.

## Sprint 3: Specialized RAG Interfaces With Local Mock Indexes

**Goal**: Create retrieval boundaries before any model integration.

**Deliverables**
- Interfaces for ServiceNow Platform RAG, Instance Metadata RAG, Project Context RAG, and Compliance RAG.
- Local deterministic/mock retrieval implementation.
- Citation model with source, version/date, confidence, and content hash.
- Retrieval failure behavior that routes to manual review.

**Tests First**
- Each RAG returns citations in the required schema.
- Missing compliance context blocks candidate generation.
- Retrieval cache keys include source hash and prompt/schema version.
- Cross-domain retrieval cannot leak instance metadata into compliance results.

**Assumptions to Challenge**
- Separate RAGs are worth the complexity versus one general index.
- Local mock indexes are enough to validate orchestration before approved vector storage.

**Exit Criteria**
- Candidate workflow can request domain-specific context without knowing storage details.
- Retrieval behavior is deterministic in tests.

## Sprint 4: Candidate Generation Without External Models

**Goal**: Generate safe JSON `UpdateSetCandidate` artifacts using templates only.

**Deliverables**
- Template-based candidate generator for the first narrow story type, likely label/help-text/content-only changes.
- Candidate artifact writer.
- Run manifest writer.
- Reviewer notes, assumptions, test suggestions, rollback notes, citations, and artifact hash.

**Tests First**
- Eligible content-only story generates a valid candidate.
- Candidate includes citations, assumptions, reviewer notes, and hash.
- Unsupported story type routes to manual build.
- Writer never overwrites an existing artifact without explicit run identity.

**Assumptions to Challenge**
- Template-only generation can produce enough value before model integration.
- JSON candidate review should precede XML generation.

**Exit Criteria**
- End-to-end mock run ingests stories, classifies them, retrieves context, and emits candidate JSON.
- 90% coverage gate remains enforced.

## Sprint 5: Provider Adapter and Model-Gated Generation

**Goal**: Add model capability without weakening compliance controls.

**Deliverables**
- Provider adapter interface.
- Rules-only provider implementation.
- Mock approved model provider for tests.
- Policy enforcement before every provider call.
- Prompt versioning and prompt input minimization.

**Tests First**
- Disallowed provider task fails before prompt construction.
- Disallowed data class fails closed.
- Approved mock provider receives only minimized fields.
- Model response schema validation rejects invented tables, unknown sys_ids, and unsafe operations.

**Assumptions to Challenge**
- Now Assist should be default only if it is available and sufficient inside the boundary.
- External providers are optional plug-ins, not architectural dependencies.

**Exit Criteria**
- No model call path exists without policy enforcement and audit metadata.
- Rules-only mode remains fully functional.

## Sprint 6: Prioritization, Repointing Suggestions, and Metrics

**Goal**: Add backlog ordering and measurable operational feedback.

**Deliverables**
- Priority scoring engine.
- Repointing suggestion engine with evidence.
- Metrics collector for automation rate, manual-review reasons, retrieval coverage, latency, and model cost placeholders.
- Run summary report.

**Tests First**
- Priority score uses business value, urgency, alignment, recency, effort, and risk.
- Repointing never mutates original story points silently.
- Metrics report counts eligible, rejected, manual-review, and generated candidates.
- Missing scoring fields degrade predictably.

**Assumptions to Challenge**
- Prioritization belongs in MVP if candidate generation is still narrow.
- Formula weights are product decisions, not engineering facts.

**Exit Criteria**
- Mock backlog produces an ordered, explainable run report.
- Metrics expose where automation is failing.

## Sprint 7: Review Workflow and Controlled Export Preparation

**Goal**: Create the minimal review workflow before XML export or UI polish.

**Deliverables**
- CLI review commands for approve, reject, and mark manual build.
- Review event log with reviewer identity, decision, timestamp, and reason.
- Optional XML candidate preparation behind an explicit feature flag.
- Export preflight checks.

**Tests First**
- Draft candidates cannot be exported.
- Approved-for-export candidates require named reviewer identity.
- Rejected candidates cannot be approved without a new revision.
- XML flag defaults off.

**Assumptions to Challenge**
- CLI review is enough before a web dashboard.
- XML should remain gated until JSON review quality is proven.

**Exit Criteria**
- Full local workflow exists from mock ingestion through review decision.
- No live ServiceNow mutation is possible.

## Sprint 8: ServiceNow Sandbox Integration

**Goal**: Replace mock ingestion with approved read-only ServiceNow sandbox ingestion.

**Deliverables**
- ServiceNow Table API client with OAuth 2.0.
- Read-only ingestion for stories and related context.
- Field allowlist and redaction layer.
- Integration tests using recorded/sanitized fixtures or approved sandbox.

**Tests First**
- Client builds expected query parameters without credentials in logs.
- Redaction removes secrets and unnecessary sensitive fields.
- API failures produce retryable/manual-review errors.
- Ingestion maps records into validated schemas.

**Assumptions to Challenge**
- Basic Auth should not be used unless explicitly approved.
- Sandbox data classification matches what local tests assume.

**Exit Criteria**
- Approved sandbox data can flow into the existing pipeline without changing core business logic.
- Secrets never appear in artifacts, prompts, logs, or test fixtures.

## Sprint 9: Hardening, Documentation, and ATO Readiness Package

**Goal**: Prepare the MVP for serious review by engineering, security, and product stakeholders.

**Deliverables**
- Threat model.
- Data flow diagram.
- Security control mapping draft.
- Operator guide.
- Developer guide.
- Test evidence and coverage report.
- Risk register and unresolved decisions list.

**Tests First**
- Documentation examples execute where practical.
- Security checks verify no public provider is enabled by default.
- Regression tests cover prior rejected assumptions and defect fixes.

**Assumptions to Challenge**
- The MVP is ready for broader review only if evidence supports it.
- Remaining manual steps are acceptable only when explicitly documented.

**Exit Criteria**
- Stakeholders can inspect the system, evidence, risks, and limits without reading source code first.
- Coverage and quality gates pass from a clean checkout.

---

## Implemented Extension Sprints

Current MVP roadmap status: implemented.

The project continued beyond the original Sprint 0-9 baseline to close the SPM-aware sidecar, controlled writeback, lifecycle orchestration, retrieved Update Set handoff, and read-only admin console roadmap. Each implemented extension sprint has a dedicated change log under `docs/sprints/`.

## MVP Baseline: Complete Through Sprint 101

The MVP is now organized into six delivery phases. This keeps the detailed sprint history intact while making the product shape easier to reason about.

| Phase | Sprints | Implemented Outcome |
|---|---:|---|
| Foundation and governance | 0-9 | Test-first baseline, 90% coverage gate, FedRAMP-aligned boundary assumptions, typed schemas, deterministic safety gates, RAG boundaries, provider gates, review workflow, and read-only ServiceNow OAuth integration. |
| Local pipeline and controlled story writeback | 10-27 | End-to-end local pipeline, context enrichment, first dictionary/form candidate, SPM/PPM work-surface decision, controlled story writeback, actor/audit capture, idempotency, batch writeback, and Sprint 27 manifest alignment for Controlled story writeback. |
| Implementation packet and candidate artifacts | 28-42 | PDI lifecycle smoke, LLM implementation packet, provider output contract hardening, validated Update Set candidate artifacts, batch candidate generation, dry-run lifecycle smoke, bootstrap field planning/apply, structured writeback verification, and writeback batch reporting. |
| Delivery handoff and lifecycle bootstrap | 43-67 | Artifact handoff reports, delivery attachment planning, reviewed delivery artifacts, Reviewed delivery lifecycle manifest, external build-result contract, ServiceNow lifecycle event contract, Business Rule/webhook bootstrap, lifecycle apply, and lifecycle verification. |
| Hosted runtime and operational store | 68-82 | Durable operational store, Sprint 69 PostgreSQL operational store retarget, lifecycle Webhook API, fulfillment worker, build-claim handler, runtime wiring, containerized runtime, Railway public webhook verification, worker loop, ChatGPT adapter boundary, and DB-backed artifact retrieval. |
| ServiceNow-native handoff, UAT, and admin visibility | 83-101 | Retrieved Update Set handoff, platform-generated customer updates, generic dictionary/form capability, reference-field support, read-only AI handoff fields, UAT Complete/Ready/Draft closeout, deterministic context escalation, admin summary APIs, and Sprint 101 Read-only admin console. |

### Detailed Sprint Index

| Sprint | Implemented Outcome |
|---|---|
| Sprint 10 | End-to-end local pipeline and safe summary output |
| Sprint 11 | Live PDI read-only pipeline mode |
| Sprint 12 | Context enrichment and affected-table inference |
| Sprint 13 | Dictionary/form candidate generation for `STRY0010013` |
| Sprint 14 | SPM/PPM workflow alignment and ServiceNow work surface decision |
| Sprint 15 | Policy-gated writeback planner and PATCH primitive |
| Sprint 16 | Instance state discovery from `sys_choice` |
| Sprint 17 | Dry-run writeback planning CLI |
| Sprint 18 | Structured field discovery from `sys_dictionary` |
| Sprint 19 | Confirmed apply gate |
| Sprint 20 | Service/human actor audit identity and writeback audit artifacts |
| Sprint 21 | `execute_writeback()` orchestration boundary |
| Sprint 22 | Local and remote writeback idempotency |
| Sprint 23 | Writeback capability preflight |
| Sprint 24 | Batch writeback orchestration |
| Sprint 25 | External build-result writeback job file ingestion |
| Sprint 26 | Batch report artifacts |
| Sprint 27 | Manifest alignment for Controlled story writeback |
| Sprint 28 | PDI lifecycle smoke confidence and current story workflow validation |
| Sprint 29 | LLM implementation packet CLI and read-only PDI story source |
| Sprint 30 | Provider output contract hardening with tests and rollback requirements |
| Sprint 31 | Validated Update Set candidate handoff and stable artifact hashes |
| Sprint 32 | Candidate builder CLI for explicit provider responses |
| Sprint 33 | Batch implementation candidate runner |
| Sprint 34 | Candidate batch report artifacts |
| Sprint 35 | Candidate batch failure isolation |
| Sprint 36 | Dry-run lifecycle smoke through writeback planning |
| Sprint 37 | Bootstrap field planning for controlled writeback fields |
| Sprint 38 | Bootstrap field apply with confirmation gates |
| Sprint 39 | Structured writeback verification |
| Sprint 40 | Apply lifecycle manifest verification |
| Sprint 41 | Writeback batch idempotency and audit behavior |
| Sprint 42 | Writeback batch CLI and reports |
| Sprint 43 | Artifact handoff report contract |
| Sprint 44 | Artifact handoff evidence hashing and fail-closed missing files |
| Sprint 45 | Artifact handoff work-note summary writeback |
| Sprint 46 | Delivery attachment gate through the ServiceNow Attachment API |
| Sprint 47 | Delivery artifact smoke path for attachment planning |
| Sprint 48 | Delivery attachment audit records |
| Sprint 49 | Delivery contract gate requiring `reviewed_export` |
| Sprint 50 | Reviewed delivery artifact job writer |
| Sprint 51 | Reviewed delivery smoke path |
| Sprint 52 | Delivery artifact hash verification before attach |
| Sprint 53 | Dry-run delivery hash preflight |
| Sprint 54 | Missing delivery artifact fail-closed preflight |
| Sprint 55 | Reviewed Update Set XML `sys_update_xml` marker gate |
| Sprint 56 | Reviewed delivery lifecycle manifest |
| Sprint 57 | Roadmap refresh through reviewed delivery lifecycle |
| Sprint 58 | External build pipeline result contract |
| Sprint 59 | ServiceNow lifecycle event contract |
| Sprint 60 | Local lifecycle event processor CLI |
| Sprint 61 | Build claim writeback planner |
| Sprint 62 | Build claim writeback execution |
| Sprint 63 | Lifecycle Business Rule bootstrap planning |
| Sprint 64 | Lifecycle webhook bootstrap bundle |
| Sprint 65 | Lifecycle ServiceNow record plan |
| Sprint 66 | Lifecycle webhook apply |
| Sprint 67 | Lifecycle webhook verification |
| Sprint 68 | Durable operational store boundary |
| Sprint 69 | PostgreSQL operational store retarget |
| Sprint 70 | Lifecycle Webhook API intake |
| Sprint 71 | Fulfillment worker claim boundary |
| Sprint 72 | Build-claim fulfillment handler |
| Sprint 73 | Runtime environment wiring |
| Sprint 74 | Containerized local runtime |
| Sprint 75 | Container lifecycle smoke and packaged runtime fixes |
| Sprint 76 | Public lifecycle webhook bootstrap verification |
| Sprint 77 | Worker loop, failure work notes, and OpenAI adapter boundary |
| Sprint 78 | Runtime ChatGPT/OpenAI implementation-candidate generation |
| Sprint 79 | Hosted long-running worker and live WIP build claim |
| Sprint 80 | Provider failure diagnostics and redaction |
| Sprint 81 | DB-backed implementation packet and candidate artifacts |
| Sprint 82 | Admin artifact retrieval API |
| Sprint 83 | Native ServiceNow Update Set handoff record |
| Sprint 84 | Controlled platform-generated customer updates |
| Sprint 85 | Story form placement correction |
| Sprint 86 | Retrieved Update Set handoff instead of local Update Sets |
| Sprint 87 | Retrieved Update Set customer update import path |
| Sprint 88 | Retrieved Update Set importer verification |
| Sprint 89 | Server-side XML import method for retrieved Update Sets |
| Sprint 90 | Live retrieved Update Set handoff proof for `STRY0010013` |
| Sprint 91 | Ready for Testing transition after retrieved Update Set handoff |
| Sprint 92 | Manual-build and failure-state handling |
| Sprint 93 | Capability-based automation gate and generic dictionary/form support |
| Sprint 94 | Deterministic context sufficiency metadata |
| Sprint 95 | Problem-table vendor reference field UAT support |
| Sprint 96 | Read-only AI handoff metadata fields |
| Sprint 97 | UAT Complete lifecycle closeout |
| Sprint 98 | UAT rework and story rejection lifecycle handling |
| Sprint 99 | Deterministic context escalation planning |
| Sprint 100 | Admin operational summary endpoints |
| Sprint 101 | Read-only admin console |

Controlled story writeback is now explicitly scoped to build claim, external build completion evidence, retrieved Update Set handoff metadata, UAT lifecycle closeout, and `Ready for Testing` transition handling. Direct production promotion, autonomous approval, and unvalidated ServiceNow mutation remain out of scope.

## Current MVP Runtime

The current product boundary is the public API and worker runtime. The sidecar can accept ServiceNow lifecycle webhook events, claim fulfillment jobs asynchronously, move a story to Work in Progress, generate an implementation packet, call the explicitly configured ChatGPT/OpenAI provider, validate implementation candidates, create retrieved Update Set handoffs, write Ready for Testing back to ServiceNow, and expose read-only operational visibility through `/admin`.

- API: receive ServiceNow lifecycle webhook events, validate payloads, persist `lifecycle_events`, enqueue `fulfillment_jobs`, serve admin summary APIs, and serve the Basic-auth read-only admin console.
- Worker: claim queued jobs using PostgreSQL `SELECT ... FOR UPDATE SKIP LOCKED`, run evaluation/build orchestration asynchronously, write state transitions and failures back to ServiceNow, and record job status in PostgreSQL.
- Runtime: package the API, worker, and PostgreSQL dependency for Railway and local container deployment with explicit environment variables and health checks.
- Evidence: preserve lifecycle manifests, implementation packets, candidate artifacts, build results, writeback audits, reviewed delivery jobs, handoff reports, retrieved Update Set references, and admin-visible operational summaries.

## Post-MVP Sprint Backlog

These are the next organized sprints. They are intentionally hardening-first: the MVP should not expand its mutation surface until authentication, observability, and evidence quality are stronger.

| Priority | Proposed Sprint | Goal | Exit Criteria |
|---:|---|---|---|
| 1 | Sprint 102: ServiceNow role-backed admin authentication | Replace or wrap local Basic auth with ServiceNow/OIDC-backed operator authentication and explicit admin-role checks. | `/admin` access is tied to customer identity, local Basic auth is development-only, and tests cover unauthenticated, unauthorized, and authorized users. |
| 2 | Sprint 103: Authenticated inbound webhook protection | Protect `/lifecycle/events` before any non-PDI use. | ServiceNow lifecycle calls use a signed secret or OAuth-authenticated integration path; unauthenticated lifecycle events are rejected. |
| 3 | Sprint 104: Confidence-based context retrieval worker | Turn deterministic context escalation into an actual retrieval step before model generation. | Missing live instance context triggers a retrieval worker; insufficient context routes to human review; the model is not asked to guess. |
| 4 | Sprint 105: Admin console drill-down and evidence views | Make the console useful for operations without adding mutation controls. | Job detail, lifecycle event detail, artifact links, and retrieved Update Set links are visible from the console. |
| 5 | Sprint 106: ATO evidence refresh | Refresh data flow, threat model, control mapping, risk register, and sprint evidence index after MVP completion. | Security docs reflect Railway dev deployment, ServiceNow sidecar flow, ChatGPT evaluation boundary, PostgreSQL artifacts, and residual risks. |
| 6 | Sprint 107: Broader capability backlog design | Decide the next supported ServiceNow change capability after generic dictionary/form placement. | A written ADR names the next capability, unsupported cases, validation requirements, and UAT story shape before implementation. |

## Next Roadmap Focus

1. Treat Sprint 101 as the MVP cut line.
2. Run no new mutation features until Sprint 102 and Sprint 103 close the authentication gaps.
3. Build Sprint 104 before expanding model autonomy; context retrieval is the root engineering step for safer LLM fulfillment.
4. Keep the admin console read-only until the operator action model is explicitly designed.
