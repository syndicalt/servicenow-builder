# Codebase Analysis & Roadmap Opportunities

**Date**: 2026-06-11
**Scope**: Full review of the codebase and documentation at Sprint 161. Summarizes current state, existing roadmap items, optimization opportunities, and proposed new roadmap items — with emphasis on full Flow Designer and Catalog Item build automation.

---

## 1. Current State

The project is a FedRAMP-aligned ServiceNow delivery sidecar: it ingests `rm_story` records via authenticated lifecycle webhooks, runs deterministic safety/capability gates, retrieves live instance context, optionally calls an approved LLM (OpenAI structured-output is the only implemented provider), and produces reviewable Retrieved Update Set candidates. Humans commit everything in ServiceNow's preview/commit boundary.

The MVP cutline was Sprint 101. As of Sprint 161 the system includes:

- PostgreSQL-backed operational store and fulfillment workers
- Split PM/source and DEV/target ServiceNow instances (Sprint 160)
- HMAC-signed lifecycle webhooks
- Read-only admin console (production role-backed auth still reserved)
- Structured model output contract — raw XML from models is rejected (Sprint 156)
- Classifier gate runtime toggle for exploratory reasoning (Sprint 158)
- Public web documentation retrieval, worker-only, HTTPS allowlist, fail-closed (Sprint 161)

### Automation surface maturity

From `src/jedi_devproject/implementation_packet.py` (`_builder_maturity_for_surface`, handoff threshold `AUTOMATED_HANDOFF_BUILDER_MATURITY_THRESHOLD = 0.75`):

| Surface | Maturity | Status |
|---|---|---|
| Dictionary field + form layout | 0.95 | Handoff enabled (hardened) |
| UI Policy (declarative subset) | 0.95 | Handoff enabled (Sprint 161) |
| Catalog item + variables | 0.60 | Candidate-only — **demoted below threshold in Sprint 161** |
| Form section (remove only) | 0.30 | Candidate-only |
| Business rule / script include / client script | 0.0 | Candidate generation, hardened validators, no handoff |
| CMDB IRE | 0.0 | Analysis + candidate only |
| Flow Designer | 0.0 | Contract/validators only, builder stubbed |

### Docs/code drift (flag)

Sprint 149–151 logs and the catalog design spec (`docs/superpowers/specs/2026-05-15-catalog-item-employee-center-design.md`) state catalog handoff is "fully enabled," but the code routes catalog candidates to manual review because 0.60 < 0.75. The code is current; the sprint docs overstate it. The sprint record should be reconciled with actual routing behavior.

---

## 2. Existing Roadmap Items (documented, not yet done)

Sourced from `docs/production-hardening-backlog.md`, `docs/risk-register.md`, `docs/system-architecture.md` (Current Gaps), and `SPRINTS.md`:

- **Flow Designer staged plan (Sprints 124–138 design)** — the 15-stage evidence pipeline exists (graph retrieval, diff contract, XML shape repository `flow-xml-shapes-v1`, naming strategy, snapshot strategy, preview/commit boundary, readiness contract), but `flow_builder_readiness_contract()` always reports not-ready. Remaining: collect real XML shape evidence and build the actual builder.
- **Business rule / client script / script include handoff** — generation and validators are done; blocked on executable-code XML evidence and validator approval (Sprints 114–121 arc).
- **CMDB IRE generation → handoff** — awaiting IRE XML shape evidence (Sprint 159 added analysis only).
- **Production admin auth** — `/admin` fails closed; role-backed OIDC/ServiceNow OAuth is documented but unimplemented (reserved since Sprint 102).
- **Slop review + security review gates** — explicitly scheduled for after the hardening backlog closes; the backlog lists the checklist (module splits, duplicate logic, webhook replay analysis, secrets audit).
- **Phase 3 review console** (README roadmap) — minimal web review workflow, approve/reject feedback capture, metrics dashboard.
- **Product Delivery Orchestration Suite** (`docs/product-delivery-orchestration-suite.md`) — the long-horizon vision: supervisor/router plus specialist agent workbenches (requirements, architecture, QA, integration, DevOps, docs, compliance) around ServiceNow as the work surface, with a typed artifact lifecycle (RequirementContract → SolutionBlueprint → … → DeliveryManifest). Today's system implements only the Implementation Configurator slice.

---

## 3. Optimization Opportunities

### Code structure

Five modules exceed 1,000 lines and mix concerns:

| Module | Lines | Suggested split |
|---|---|---|
| `cli.py` | 1,540 | Thin CLI orchestrator + per-pipeline stage modules |
| `instance_discovery.py` | 1,407 | Split by surface type (schema, form layout, scripts, flows, CMDB, docs) |
| `runtime.py` | 1,365 | Config, auth, admin routes, worker lifecycle |
| `capability_analysis.py` | 1,277 | Extract intent classifier and capability profiles |
| `bootstrap.py` | 1,013 | Fields, business rules, importer |

Splitting discovery by surface type and extracting the intent classifier would help most, since those are the files every new capability touches.

### Duplication

- All six generation modules hand-craft XML with string concatenation and `escape()`. A shared `xml_builder.py` would remove ~200 lines and give the Flow Designer and CMDB IRE builders a vetted foundation instead of a seventh copy.
- The intent-extraction pattern and field-parsing helpers (`_string_list()`, `_bool_value()`, `_bool_text()`) repeat across 4+ modules; a shared `validation_helpers.py` plus a generic intent extractor removes another ~150 lines.

### Runtime efficiency

- **RAG retrieval has no caching** — runs per-story despite the README requiring caching by source hash.
- **Silent context truncation** — `MODEL_CONTEXT_RECORD_LIMIT = 25` and a 3-section limit truncate without telling the model it saw a partial picture. Surfacing elisions in the packet would improve candidate quality on large surfaces.
- **No retention/archival policy** for Postgres `artifact_blobs`; large implementation packets accumulate unbounded.

### Maturity scoring

`_builder_maturity_for_surface()` is a hardcoded constant table, yet maturity now gates handoff routing. Making it **evidence-driven** — derived from UAT pass/fail and reviewer approval rates already captured in the operational store — turns the threshold from an opinion into a measurement, and creates the natural promotion path for catalog and the code surfaces.

### Docs hygiene

Reconcile the Sprint 149–151 catalog handoff claims with the Sprint 161 demotion so the sprint record matches routing behavior.

---

## 4. New Roadmap Items

### 4.1 Catalog Item: full build automation (nearest, highest-leverage win)

The core builder (`catalog_item_generation.py`) handles `sc_cat_item`, `item_option_new`, category links, and Employee Center connected content. What "full" requires, roughly in dependency order:

1. **Reference qualifier serialization** — the intent model accepts qualifiers but they don't reach the XML payload. Small change; unblocks reference variables that actually filter.
2. **Catalog UI policies** (`catalog_ui_policy` / `catalog_ui_policy_action`) — conditional variable visibility/mandatory. The hardened, handoff-enabled UI policy builder for forms already exists; this is an adaptation to the catalog variant tables, not new ground.
3. **Catalog client scripts** (`catalog_script_client`) — onChange/onLoad on item variables, reusing the existing `g_form` validator suite.
4. **Variable sets and container grouping** (`item_option_new_set`, container_start/end variables) — today variables render as a flat list.
5. **Record producers** as a sibling capability — same table family, large share of real catalog stories.
6. **Evidence-driven maturity promotion** — with items 1–4 plus UAT evidence, catalog crosses 0.75 legitimately and handoff re-enables.

### 4.2 Flow Designer: from contract to builder

The 15-sprint design arc means the safety scaffolding already exists — what's missing is evidence and the builder itself:

1. **XML shape evidence collection** — capture real `sys_hub_flow`, `sys_hub_action_instance`, `sys_hub_flow_logic_instance_v2`, and snapshot customer-update XML from the DEV PDI and validate against the `flow-xml-shapes-v1` repository.
2. **Deterministic graph-diff → customer-update builder** for the approved narrow subset: one additive action or one condition change on a single record-triggered flow. The `FlowGraphDiffIntent` contract and hash-stability validators are already in place.
3. **Snapshot strategy implementation** — the `latest_snapshot` evidence requirement is specified but not coded.
4. **PDI round-trip harness** — build → import as Retrieved Update Set → re-retrieve graph → assert the diff matches intent. This is the UAT shape that lets the readiness contract flip from always-false to per-evidence.
5. **Staged expansion** once the modify path is proven: new record-triggered flow creation from templates (no custom actions/spokes/subflows), then condition-branch additions.

### 4.3 Convergence milestone: catalog fulfillment flows

The most valuable single capability neither track delivers alone: attaching a fulfillment flow to a generated catalog item (`sc_cat_item.flow_designer_flow`). A "create catalog item with approval-then-task fulfillment" story is the canonical real-world request, and it falls out naturally once catalog reaches full automation and flow creation reaches its template subset. Worth naming as an explicit roadmap milestone so both tracks design toward it.

### 4.4 Other candidates

- **ATF test generation** alongside candidates — closes the loop on the "test suggestions" the contract already requires, and feeds the evidence-driven maturity model.
- **Second provider adapter** (Bedrock/Anthropic via a GovCloud-approved path) — the provider registry design anticipates it; today OpenAI is a single point of policy failure.
- **Feedback-driven story rewriting at intake** — Sprint 157's rewrite suggestions could move upstream into the intake flow, raising the share of stories that pass gates at all.

---

## 5. Recommended Sequencing

1. **Catalog completion** (items 4.1.1–4.1.4) — weeks, not months, and reuses hardened builders.
2. **Evidence-driven maturity scoring** — the promotion mechanism everything else needs.
3. **Flow Designer evidence collection** — in parallel; mostly PDI data gathering.
4. **Flow builder** for the narrow modify subset.
5. **Convergence milestone** — catalog item + fulfillment flow.
