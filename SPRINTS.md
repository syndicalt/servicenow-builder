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

The project continued beyond the original Sprint 0-9 baseline to close the SPM-aware sidecar and controlled writeback roadmap. Each implemented extension sprint has a dedicated change log under `docs/sprints/`.

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

Controlled story writeback is now explicitly scoped to external build completion evidence and `Ready for Testing` transition handling. Direct Update Set imports, deployments, production promotion, and unvalidated ServiceNow mutation remain out of scope.
