# ADR 0012: Knowledge Foundation Capability Family

## Status

Proposed.

## Context

The Knowledge Foundation engagement (see `docs/knowledge-foundation-sow-analysis.md`)
introduces a new artifact domain: ServiceNow Knowledge Management configuration and the
knowledge content lifecycle — inventory, disposition, transformation, migration, and external
source indexing. Every capability shipped to date generates platform *configuration* records.
Knowledge work adds two things the pipeline has never handled: **content as the artifact**
(articles with prose bodies, not declarative field sets) and **authenticated external content
sources** (SharePoint via Microsoft Graph, WordPress, Azure Blob Storage) beyond the
allowlisted public-web retriever.

Treating knowledge as a small variant of catalog generation would create three hidden risks:
content-quality failures that no schema validator catches, data-classification exposure when
external HR content reaches a model, and access-control drift if knowledge access rules are
conflated with the platform ACL surface that the safety gates correctly reject.

No `kb_*` table is currently on any allowlist. No external authenticated connector exists.
The default disposition for all of this work is therefore manual review, and this ADR defines
the staged path out of that default.

## Decision

Define the knowledge foundation capability family. No runtime generation is enabled by this
ADR. Capabilities are introduced in four stages, each gated on the evidence pattern
established by ADR 0006 (capability extension) and proven by ADR 0011 (Flow Designer):
analysis before generation, shape evidence before XML, candidate generation before handoff,
recorded UAT evidence before maturity promotion.

### Stage 1 — Knowledge source analysis (read-only, no mutation surface)

New capabilities `knowledge_source_inventory` and `knowledge_disposition_analyze`.

- Read-only authenticated source connectors for SharePoint (Microsoft Graph), WordPress
  (REST), and Azure Blob Storage, plus read-only `kb_knowledge` retrieval from a legacy
  ServiceNow source instance (a third instance role extending the Sprint 160 split-instance
  model). Connectors follow the public-web retriever contract: explicit allowlist per source,
  HTTPS only, bounded fetches, content hashes for audit, fail closed when access, metadata,
  or security-trimming inputs are missing. Credentials are operator-provisioned secrets;
  the pipeline never generates, stores, or writes back authentication material.
- Inventory artifacts (`knowledge-inventory-v1`) normalize each source artifact: title,
  owner, age, location, metadata completeness, source category.
- The AI-readiness rubric scorer applies the engagement standards (title clarity,
  answer-first structure, metadata, ownership, review cadence, source-of-truth attribution)
  as deterministic checks first; model-assisted scoring runs only for judgment dimensions and
  only when the provider policy permits the content's data class. Scores carry rationale and
  citations (`knowledge-readiness-score-v1`).
- Disposition recommendation artifacts (`knowledge-disposition-recommendation-v1`) propose
  MIGRATE, CONNECT, REAUTHOR, or RETIRE per artifact with rationale. Recommendations are
  evidence for the human-signed Disposition Plan; they are never self-executing.

Data classification boundary: external content enters the model path only after its data
class is mapped in the provider policy. HR and Benefits content is presumed sensitive until
classified otherwise; unclassified content fails closed to deterministic-only scoring.

### Stage 2 — Knowledge migration pipeline (candidate generation, no handoff)

New capability `knowledge_article_migrate`, driven exclusively by a signed Disposition Plan
ingested as machine-readable configuration (`knowledge-disposition-plan-v1`). No article is
processed without a plan entry naming it MIGRATE or REAUTHOR.

- The deterministic scrubbing/substitution engine applies a versioned term map (SAP →
  Workday), link rewriting, and stale-reference detection. The ruleset is itself a reviewed,
  versioned artifact; every substitution is recorded per article for audit.
- MIGRATE articles flow: legacy extraction → scrub/substitute → `kb_knowledge` candidate with
  the AI-readiness metadata standards applied (ownership, review cadence, attribution).
- REAUTHOR articles additionally run the implementation-packet pipeline with a knowledge-
  domain retrieval index grounding the rewrite in the agreed standards. The output contract
  requires citations, assumptions, and manual review when uncertain — identical governance to
  update-set candidates.
- Batch jobs reuse the fulfillment worker model with per-article content-hash idempotency.
  Publication remains human: candidates surface for review; the knowledge publication
  workflow in ServiceNow is the commit boundary, mirroring the Retrieved Update Set
  preview/commit boundary for configuration.

### Stage 3 — Knowledge configuration builders (candidate generation, evidence-gated handoff)

New capabilities `knowledge_base_create`, `knowledge_category_structure`,
`knowledge_article_template_create`, and `knowledge_feedback_config`.

- Deterministic builders following the catalog item pattern: typed normalized intent,
  fail-closed discovery (workflow references, owners, and taxonomy nodes must resolve
  uniquely against the live instance), stable sys_ids, byte-stable payloads.
- Publication/review/retirement workflow support is limited to **selecting existing
  workflows** discovered on the instance. Authoring new flows is the Flow Designer
  capability's job and inherits its evidence gates; this family never embeds flow logic.
- A `kb-xml-shapes-v1` shape repository and evidence collector (the ADR 0011 pattern) gate
  any retrieved Update Set handoff. Until per-instance shape evidence is collected and
  validated, these capabilities are candidate-generation only.
- Builder-maturity surfaces enter at 0.30. Promotion requires recorded UAT evidence through
  the evidence-driven maturity mechanism; field failures demote.

### Stage 4 — Access rules, indexing configuration, and analytics

- **Knowledge access rules** (`knowledge_access_rules_attach`): the ONLY access-control
  surface this family may touch is `user_criteria` attachment to knowledge bases via
  `kb_uc_can_read_mtom` / `kb_uc_can_contribute_mtom`, referencing **existing, discovered**
  user criteria records. Creating user criteria, modifying ACLs, roles, or groups remains
  default-rejected exactly as today. Any story mixing knowledge access with platform
  access-control language routes to manual review with a stable reason code.
- **Indexing configuration** (`knowledge_search_source_config`): declarative AI Search
  source and indexing-pattern records, generated only after a dedicated shape-evidence
  repository for the search-source tables is collected and validated. Authentication,
  Graph consent, and security-trimming wiring are operator tasks, routed with stable reason
  codes — never generated.
- **Analytics definitions** (`knowledge_analytics_config`): Performance Analytics indicator
  and report definitions for search performance, zero-result trends, feedback signals,
  content gaps, and article quality. Declarative records, candidate generation first. The
  improvement loop closes upstream: zero-result and gap artifacts feed Stage 1's disposition
  analysis as REAUTHOR/new-article evidence.

### Supported first subset (when stages activate)

- One knowledge base, or one category structure, or one article template per story.
- One source artifact per migration candidate; batches are compositions of single-artifact
  candidates, individually reviewable.
- Existing workflows, existing user criteria, existing taxonomy nodes only — discovered,
  never invented.
- Deterministic substitutions from the versioned term map only; free-form model rewrites
  route to REAUTHOR review.
- All generated changes represented as reviewable artifacts; ServiceNow-native review
  (knowledge publication workflow or Retrieved Update Set preview/commit) remains the human
  boundary.

### Forbidden cases

- ACL, role, or group mutation of any kind.
- User criteria creation or modification.
- Credential, consent, or security-trimming configuration.
- Autonomous publication or retirement of any article.
- Disposition execution without a signed, ingested Disposition Plan entry.
- Model exposure of content whose data class is unmapped in the provider policy.
- Workflow/flow authoring inside this family (Flow Designer capability owns it).
- Writeback to source systems (SharePoint, WordPress, Azure) — connectors are read-only,
  permanently.

## Consequences

- The engagement's workshop timeline gets evidence tooling first (Stage 1 is read-only and
  carries no mutation risk), while the highest-effort build (Stage 2) is driven by an
  artifact — the signed Disposition Plan — that the engagement produces anyway.
- The pipeline gains its first content-artifact type and its first authenticated external
  connectors; both reuse existing compliance patterns (allowlists, fail-closed, hashes,
  worker-only execution) rather than inventing parallel ones.
- Knowledge access rules get a deliberately narrow, auditable path instead of either
  weakening the platform access-control rejection or blocking the engagement entirely.
- Four new allowlist families, four new shape repositories at most, and a set of 0.30
  maturity surfaces extend the existing governance machinery without modifying it.
- Nothing in this ADR enables runtime generation; each stage activates through the same
  design → analysis → evidence → candidate → earned-handoff progression already proven by
  the Business Rule, UI Policy, Catalog, and Flow Designer families.
