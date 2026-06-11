# Knowledge Foundation SOW — Pipeline Development Analysis

**Date**: 2026-06-11
**Status**: Analysis complete; capability design proposed in [ADR 0012](adr/0012-knowledge-foundation-capability-family.md)
**Scope**: Maps the AI-augmented employee services Knowledge Foundation SOW onto the JEDI development pipeline (post-Sprint 163) and identifies what must be developed to facilitate automated delivery.

---

## 1. Engagement Summary

The SOW establishes a ServiceNow knowledge foundation for AI-augmented employee services:
knowledge structure, taxonomy, governance workflow, AI-readiness standards, content migration
and connection rules, and analytics. Content is organized into four customer-defined source
categories with default dispositions:

| Category | Content | Sources | Default disposition |
|---|---|---|---|
| 1 — Workday Training Content | Reference guides, videos, e-learnings | SharePoint, WordPress, Azure blob | CONNECT (indexed in place) |
| 2 — Policy Sites | University and Health policy content | Source-of-truth sites | CONNECT |
| 3 — HR and Benefits Sites | University and Health HR/Benefits sites | Source sites | CONNECT |
| 4 — Current Functional Knowledge | Legacy ServiceNow instance + internal sites | Legacy SN instance | MIGRATE (scrub + SAP→Workday substitution) |

Every artifact's final disposition (MIGRATE / CONNECT / REAUTHOR / RETIRE) is decided
collaboratively in a signed Disposition Plan. The consultant may recommend Category 1–3
content for MIGRATE where AI-readiness analysis supports it.

## 2. Pipeline Framing

This engagement introduces a **new artifact domain** for JEDI. Everything automated to date is
platform *configuration* (fields, forms, catalog, flows). This SOW is dominated by the
**knowledge content lifecycle** — inventory, disposition, transformation, migration, indexing —
plus a knowledge-specific configuration family (`kb_*` tables). Roughly 60% of the in-scope
services map onto JEDI's existing candidate/review/evidence architecture; the remainder is
net-new connector infrastructure or genuinely human work the SOW already assigns to people.

## 3. Development Requirements

### 3.1 Knowledge Management configuration capability family (extends existing builder pattern)

| SOW item | ServiceNow artifact | JEDI fit |
|---|---|---|
| Knowledge bases | `kb_knowledge_base` (owner, managers, workflow references) | New deterministic builder, same pattern as the catalog item builder — declarative, discovery-resolved references |
| Taxonomy / structure | `kb_category`, Employee Center taxonomy/topics | Partially exists — catalog discovery already resolves taxonomies and connected content; extend to KB categories |
| Article templates / standards | KB article templates plus mandatory metadata field standards | New builder; template records are declarative |
| Publication / review / retirement workflow | Workflow references on the knowledge base | Selecting existing workflows is declarative and low risk. Authoring new workflows lands on the Flow Designer capability — a direct dependency on the flow evidence milestone |
| Access rules | `user_criteria` + `kb_uc_can_read_mtom` / `kb_uc_can_contribute_mtom` | **Caution**: safety gates default-reject access-control changes. Requires a deliberately scoped capability — user-criteria attachment to KBs only, never ACLs or roles — designed in ADR 0012 |
| Feedback capture | KB feedback/rating properties | Declarative config builder, low risk |

All configuration builders enter at conservative maturity (candidate generation, manual
review) and are promoted only through recorded UAT evidence, per the established model.

### 3.2 Content migration pipeline (net-new pipeline type — the largest build)

Category 4 (MIGRATE with content scrubbing and SAP→Workday reference substitution) is the
highest-volume, highest-automation-value item:

1. **Legacy-instance extraction.** A third instance role. Sprint 160 split the PM/source
   instance from the DEV/target instance; this adds a read-only **legacy content source**
   instance with `kb_knowledge` discovery surfaces. The split-instance architecture was built
   for exactly this kind of extension.
2. **Deterministic scrubbing/substitution engine.** A versioned, auditable term-map ruleset
   (SAP term → Workday term), link rewriting, and stale-reference detection. Deterministic
   rules first, per the project's efficiency requirements — most substitutions must not need
   a model call.
3. **LLM-assisted reauthoring (REAUTHOR disposition).** The existing implementation-packet →
   structured-candidate → human-review loop, retargeted at article content. The output
   contract becomes rewritten article + metadata + source-of-truth citation + assumptions,
   reviewed before publication — the same governance shape as update-set candidates.
4. **`kb_knowledge` record generation.** A builder producing article records with AI-readiness
   metadata baked in (ownership, review cadence, attribution fields).
5. **Batch orchestration.** The fulfillment worker/job model handles volume; needs
   content-batch job types and per-article idempotency (content-hash keyed, the same pattern
   as intake feedback).

### 3.3 Source inventory and disposition tooling (net-new connectors, existing artifact model)

1. **Read-only authenticated source connectors**: SharePoint (Microsoft Graph), WordPress
   (REST API), Azure Blob Storage. The public-web retriever established the compliance
   pattern — allowlisted, HTTPS-only, fail-closed, content-hashed, worker-only. These are its
   authenticated siblings. Credentials follow the existing secret-management posture;
   security-trimming inputs (Graph permissions) are customer-provided per the SOW.
2. **Inventory artifact generation**: crawl → normalized inventory records (title, owner, age,
   metadata completeness, category) persisted as artifacts feeding the disposition workshops.
3. **AI-readiness rubric scorer**: the SOW rubric (title clarity, answer-first structure,
   metadata, ownership, review cadence, attribution) splits into deterministic checks
   (metadata present, owner assigned, heading structure) plus model-assisted scoring through
   the packet pipeline for judgment calls. Output: per-artifact scores with rationale.
4. **Disposition recommendation artifacts**: MIGRATE / CONNECT / REAUTHOR / RETIRE proposals
   with rationale and citations — reviewable candidates that humans finalize in the signed
   Disposition Plan. This also implements the clause allowing the consultant to recommend
   Category 1–3 content for MIGRATE: the recommendation engine produces the evidence.
5. **Disposition Plan ingester**: the signed plan becomes machine-readable configuration
   driving the migration batch jobs — the human decision is the input, never the output.

### 3.4 Connector / indexing configuration generation (declarative subset only)

"Implement connectors and indexing patterns" splits into:

- **Declarative (generatable)**: AI Search source configurations, indexing patterns,
  attribution metadata mappings — generated as reviewed candidates once XML shape evidence is
  collected for those tables. The flow-evidence collector pattern applies directly: a new
  shape repository for search-source tables, evidence before any builder.
- **Manual by design**: authentication setup, Graph API consent, security-trimming wiring.
  Credential handling is on the default-rejection list and stays there; route with stable
  reason codes.

### 3.5 Analytics definitions (small, declarative)

Zero-result trends, search performance, feedback signals, content gaps, and article quality
indicators map to Performance Analytics indicators and report definitions — declarative
records, a small builder family, low risk. The improvement *routine* closes the loop:
zero-result trend → content-gap artifact → REAUTHOR or new-article candidate.

## 4. Deliberately Human (the pipeline routes, never attempts)

- **Workshops, business ownership, SME validation, publication/retirement approval** — the
  SOW assigns these to the customer; JEDI produces the artifacts those humans review.
- **Governance role establishment** (Knowledge Owner, Gatekeeper, Steward, escalation lead) —
  roles/groups are default-rejected by the safety gates and remain so. JEDI generates
  governance documentation and assignment checklists instead.
- **Final disposition decisions** — JEDI recommends with evidence; the signed Disposition
  Plan decides.
- **Credential and consent provisioning** — Graph API access, WordPress/Azure authentication,
  source permissions are customer-provided inputs, never generated artifacts.

## 5. Recommended Build Order

| Phase | Work | Rationale |
|---|---|---|
| 1 | Disposition tooling: read-only connectors, inventory, rubric scorer, recommendation artifacts | Read-only, lowest risk, needed earliest (workshops) |
| 2 | Migration pipeline: legacy extraction, scrubbing engine, `kb_knowledge` builder, batch jobs, Disposition Plan ingester | Highest volume; Category 4 is the primary MIGRATE source |
| 3 | KB configuration builders (knowledge bases, categories, templates, feedback) + the access-rules scoped design | Standard builder family work |
| 4 | Indexing-config generation behind shape-evidence collection; analytics builders | Evidence-gated; last |

## 6. Cross-Cutting Requirements

- **Allowlists and maturity surfaces**: no `kb_*` table is currently on any allowlist; the
  domain needs its own table/operation allowlist entries and builder-maturity surfaces
  (entering at conservative baselines).
- **Data classification**: external content diversity is new. Policy sites are public; HR and
  Benefits content may carry PII implications for what reaches a model. Provider-policy data
  classes must be confirmed to cover external content before any model-assisted scoring or
  reauthoring runs against it.
- **Multi-instance configuration**: a third (legacy source) instance role extends the
  Sprint 160 split-instance model.
- **RAG**: a knowledge-domain retrieval index for the AI-readiness standards and rubrics so
  packets ground reauthoring candidates in the agreed standards with citations.

## 7. Effort Concentration (qualitative)

The migration pipeline (3.2) and source connectors (3.3.1) carry most of the engineering
effort and all of the new infrastructure risk. The configuration builders (3.1, 3.5) are
pattern-stamping on proven machinery. The disposition tooling (3.3.2–5) is moderate effort
with outsized engagement value because it front-loads the workshops with evidence.
