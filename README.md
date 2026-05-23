# jedi-devproject-0

**Version**: 0.2.0 (FedRAMP-aligned MVP)  
**Date**: May 2026  
**Author**: Nicholas Blanchard  
**Purpose**: Define a regulated, efficient AI-assisted platform that ingests ServiceNow `rm_story` records plus project context, analyzes and prioritizes work, and generates reviewable Update Set candidates for tightly scoped, low-risk stories. The system is dry-run by default and must operate inside the customer's approved Federal authorization boundary.

---

### 1. Objectives & Scope

**Primary Goals**
- Accelerate delivery for small, low-risk ServiceNow stories without bypassing human accountability.
- Generate reviewable Update Set candidates, not autonomous production changes.
- Keep developers, testers, and approvers firmly in the loop for every promoted artifact.
- Maintain traceability from story input -> retrieved context -> model decision -> generated artifact -> reviewer decision.
- Support regulated Federal environments by making model, data, logging, and hosting choices authorization-boundary driven.
- Scale from mock data -> approved ServiceNow integration -> approved model/RAG integration.

**In Scope**
- Ingestion of `rm_story` plus related project, epic, dependency, and instance metadata.
- Repointing, prioritization, ordering, and risk classification.
- Update Set candidate generation only for stories that pass explicit safety gates.
- Specialized RAG pipelines for ServiceNow knowledge, instance metadata, project context, and compliance constraints.
- Structured artifacts with proposed changes, scripts, confidence scores, reviewer notes, citations, assumptions, and audit metadata.
- Dry-run, human-review, approval, rejection, and feedback capture workflows.
- Controlled ServiceNow story writeback after external build completion, limited to allowlisted `rm_story` fields and `Ready for Testing` transition checks.

**Out of Scope (MVP)**
- Direct Update Set imports, commits, deployments, or production promotions.
- Unvalidated ServiceNow mutation outside the controlled story writeback path.
- Autonomous approval or promotion of Update Sets.
- Large, ambiguous, cross-module, data-migration, security-sensitive, or integration-heavy stories.
- Use of any model, embedding service, vector store, or logging sink outside the approved Federal authorization boundary.
- Production LLM hosting decisions without security, privacy, and ATO review.

---

### 2. Compliance Posture

This project should be treated as **FedRAMP-aligned and authorization-boundary ready**, not inherently FedRAMP compliant. Compliance depends on the deployed environment, cloud region, identity controls, model provider, data flows, logging configuration, and customer ATO package.

**Required Controls**
- **Boundary first**: Select model and storage providers only after confirming the customer environment: ServiceNow GCC/FedRAMP High, FedRAMP Moderate, DoD IL4/IL5, contractor CUI, or another boundary.
- **No public AI endpoints**: Public commercial model APIs are prohibited unless explicitly approved for the relevant boundary and data category.
- **Data minimization**: Send the smallest useful context to models. Strip secrets, credentials, tokens, unnecessary PII, and unrelated records before retrieval or generation.
- **Audit logging**: Record prompt version, model/provider, retrieval citations, input hashes, generated artifact hash, reviewer identity, approval decision, and timestamps.
- **Human approval**: No generated candidate becomes an importable/promoted Update Set without named human approval.
- **Least privilege**: ServiceNow accounts must be read-only for MVP ingestion unless a later phase receives explicit write authorization.
- **Retention control**: Prompts, outputs, embeddings, and review logs must follow agency/customer retention rules.
- **Explainability**: Every generated candidate must include source citations, assumptions, and rejection reasons when confidence is below threshold.

**Reference Authorization Signals**
- ServiceNow Now Assist and ServiceNow GCC may be preferred native options when available inside the customer's regulated ServiceNow environment.
- OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, Google, or other providers may be considered only through an approved Federal/GovCloud/FedRAMP path that matches the required impact level.
- If no approved model path exists, the MVP must run in rules-only/template-only mode.

---

### 3. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Language** | Python 3.11+ | Mature API, validation, testing, and data tooling |
| **Data Models** | Pydantic | Strict schemas, validation, and JSON serialization |
| **Storage (MVP)** | PostgreSQL operational state plus DB-backed JSON artifacts | Production-shaped event/job tracking, row-level worker claims, and durable implementation packet/candidate records |
| **Storage (Production)** | Approved PostgreSQL plus boundary-approved object storage if needed | Must match customer boundary, encryption, retention, and audit needs |
| **ServiceNow Integration** | REST Table API + OAuth 2.0 | Standard controlled ingestion for `rm_story`, `rm_epic`, project, and metadata tables |
| **Model Layer** | Provider adapter with policy allowlist | Enables Now Assist/native first, then approved external models only when authorized |
| **RAG Layer** | Specialized retrieval indexes with source citations | Reduces prompt size, improves grounding, and separates knowledge domains |
| **Orchestration** | Plain Python CLI first; Prefect/Airflow later if approved | Efficient MVP path before adding scheduler complexity |
| **UI** | Minimal review UI in Phase 2 | Human approval matters more than dashboard polish in MVP |
| **Export** | JSON candidate first; ServiceNow-compatible XML only after review | Avoids implying production readiness before validation |
| **Testing** | pytest + schema validation + ServiceNow dev/sandbox instance | Verifies artifacts before any promotion workflow |

### 3.1 Work Surface Architecture

ServiceNow is the canonical work surface and workflow system of record. Users should continue to manage demand intake, project governance, backlog refinement, sprint execution, testing, and release tracking in ServiceNow SPM/PPM and Agile Development workflows.

The detailed runtime architecture, workflow diagrams, and data-flow diagrams are maintained in `docs/system-architecture.md`.

This product operates as an SPM-aware sidecar. It monitors approved ServiceNow records, analyzes eligible stories, generates reviewable artifacts, coordinates with the external build pipeline, and writes structured status back to ServiceNow. It does not replace Demand Management, Project Management, Agile Development 2.0, sprint planning, release tracking, or human approval.

The sidecar writeback model is structured first:

- Custom fields or related records for AI status, risk score, confidence, artifact references, fulfillment route, and build completion evidence.
- Work notes or comments for human-readable summaries only.
- Attachments or artifact links for generated candidates and external build outputs.
- Story state advancement only when allowlisted lifecycle conditions pass.

The external build process is outside this project scope. When that external process reports successful build completion, this product may write back build evidence and move the story to `Ready for Testing`, provided the instance state mapping and customer policy allow the transition. Failed, blocked, or ambiguous build results route to human review without advancing the story state.

Automated writeback uses `execute_writeback()` for one external build result and `run_writeback_batch()` for job batches. Both paths perform capability preflight, state discovery, dictionary field validation, actor identity capture, idempotency checks, and write-once audit artifact creation before any ServiceNow mutation.

---

### 4. Model & RAG Architecture

#### 4.1 Provider Policy

The system must use a model-provider registry:
- `provider_id`
- `deployment_boundary`
- `authorization_level`
- `allowed_data_classes`
- `allowed_tasks`
- `max_context_policy`
- `retention_policy`
- `status`: `disabled`, `evaluation`, `approved`, `revoked`

Default provider order:
1. Approved native ServiceNow/Now Assist capability, when available and sufficient.
2. Approved Federal cloud-hosted model endpoint within the required boundary.
3. Approved on-prem/private model endpoint.
4. Rules-only/template-only fallback.

No task may call a provider unless the provider policy explicitly allows the task and data class.

#### 4.2 Specialized RAGs

Use separate retrieval paths instead of one broad vector index:

- **ServiceNow Platform RAG**: platform docs, table schemas, update set rules, scripting patterns, and approved implementation examples.
- **Instance Metadata RAG**: customer-specific tables, fields, business rules, catalog items, portal pages, UI policies, and dependency metadata.
- **Project Context RAG**: objectives, epics, constraints, acceptance criteria, stakeholders, and sprint priorities.
- **Compliance RAG**: agency policy, data handling rules, approved model/provider list, logging requirements, and prohibited actions.

Each retrieval result must include source, version/date when available, confidence, and citation metadata. Retrieval failures should degrade to manual review, not ungrounded generation.

#### 4.3 Efficiency Requirements

- Prefer deterministic classifiers and templates before model calls.
- Cache retrieval results by source hash and prompt version.
- Use small/task-specific prompts rather than one large agent prompt.
- Batch story analysis, but generate artifacts one story at a time for audit clarity.
- Track model cost, latency, token usage, retrieval hit rate, and manual-review rejection rate.
- Avoid multi-agent workflows until single-step candidate generation is reliable and measurable.

#### 4.4 LLM Implementation Packet

rules are gates, not the implementation engine. Deterministic controls decide whether a story is eligible, whether the provider is approved, what tables and operations are allowed, and whether generated output is safe. The implementation work is performed through an LLM implementation packet.

The LLM implementation packet is a model-ready, citation-backed context bundle for Now Assist or another approved provider. It includes:

- minimized story fields without ServiceNow sys_id
- safety decision and reasons
- deterministic risk score
- allowlisted tables and operations
- ServiceNow platform, instance metadata, project context, and compliance retrieval sections
- citation metadata
- structured output contract requiring manual review when uncertain

`generate_implementation_candidate()` builds the packet, sends it to the approved provider, and validates the model response against allowlisted tables, operations, and sys_id policy.

---

### 5. Core Data Models & Artifacts

#### 5.1 Story (maps to `rm_story`)
- `sys_id`, `number`, `short_description`, `description`
- `story_points`, `priority`, `state`, `project`, `epic`
- `acceptance_criteria`, `business_value`, `risk`, `effort_estimate`
- `dependencies`, `affected_tables`, `affected_applications`
- `data_classification`, `additional_context`, timestamps

#### 5.2 ProjectContext
- Name, objectives, constraints, stakeholders, key dates, success metrics
- Authorized environments, approved model providers, data handling constraints
- Definition of low-risk story types for the customer/program

#### 5.3 UpdateSetCandidate (Primary Deliverable)
- `story_number` and source record references
- `name` (example: `UPD_STORY-123_Fix_Welcome_Typo`)
- `eligibility_decision`: `eligible`, `manual_review`, `rejected`
- `eligibility_reasons`
- `changes`: list of `{table, operation, fields, sys_id?, rationale}`
- `scripts`: list of `{type, name, content, when, rationale}`
- `xml_snippet`: optional candidate XML, never treated as approved import output in MVP
- `confidence` and `risk_score`
- `retrieval_citations`
- `assumptions`
- `reviewer_notes`
- `generated_by`, `model_provider`, `model_name`, `prompt_version`, `generated_at`
- `artifact_hash`
- `status`: `Draft` -> `Ready for Review` -> `Approved for Export` -> `Rejected` -> `Manual Build`

**Artifact Storage**: One run manifest plus one candidate file per story. Store raw inputs separately from generated outputs and redact sensitive fields where required.

---

### 6. Detailed Workflows

#### 6.1 Ingestion Workflow
1. Query approved ServiceNow source tables for candidate stories and related context.
2. Pull only fields required for classification, prioritization, and candidate generation.
3. Validate records against schemas and data classification rules.
4. Persist raw input hashes and normalized records.
5. Flag missing metadata before any model call.

#### 6.2 Analysis & Prioritization Workflow
1. Use deterministic heuristics first for completeness, dependency, risk, and obvious story type.
2. Use an approved model only when policy permits the story data class and task.
3. Suggest repointing with evidence, not silent replacement of human estimates.
4. Score priority with a documented formula:

   ```text
   Score = (0.4 * Business Value + 0.3 * Urgency + 0.2 * Strategic Alignment + 0.1 * Recency) / (Effort + Risk + 0.1)
   ```

5. Sort backlog by score and separately report blockers, dependencies, and manual-review items.

#### 6.3 Candidate Generation Workflow

Trigger requires all of the following:
- `story_points <= MAX_POINTS_FOR_AUTO` (default = 3)
- story type is on the customer-approved allowlist
- affected tables are on the customer-approved allowlist
- no cross-module dependency, data migration, credential handling, security control change, or external integration
- acceptance criteria are clear enough to test
- approved model/provider exists for the data class, or a deterministic template can handle the story

For each qualifying story:
1. Classify story type using rules, retrieved context, and an approved model only when necessary.
2. Retrieve ServiceNow, instance, project, and compliance context from specialized RAGs.
3. Generate a candidate artifact using the smallest sufficient prompt/template.
4. Validate schema, table allowlist, operation allowlist, and script safety rules.
5. Calculate confidence and risk scores.
6. Generate reviewer notes, assumptions, citations, and test suggestions.
7. Output `UpdateSetCandidate` in `Draft` or `Ready for Review` state.

#### 6.4 Human Review & Promotion
- Developer reviews candidate JSON, proposed XML, citations, assumptions, and test suggestions.
- Approve -> candidate may be exported for controlled import into an approved development/sandbox instance.
- Reject -> feedback is captured, candidate is marked `Rejected` or `Manual Build`.
- Any production promotion remains outside MVP and requires existing change-management controls.

#### 6.5 Controlled Story Writeback
Controlled ServiceNow story writeback is limited to external build completion evidence and transition to `Ready for Testing`.

Required controls:
1. Discover `Ready for Testing` from `sys_choice`; do not hardcode customer state values.
2. Verify required structured fields exist on `rm_story` through `sys_dictionary`.
3. Require actor identity: service principal/workload identity for automated orchestration, or human identity for manual runs.
4. Require matching story confirmation for apply paths.
5. Write per-story audit artifacts and batch report artifacts without ServiceNow sys_ids.
6. Treat repeated local audit artifacts or matching remote story state/build reference as idempotent no-ops.

---

### 7. Business Rules

**Low-Risk Story Criteria**
- 3 points or fewer.
- Customer-approved story type.
- Customer-approved table/application scope.
- Clear acceptance criteria and rollback path.
- No sensitive data exposure, access-control change, credential handling, data migration, external integration, or platform security change.

**Confidence Scoring**
- High (`>0.85`): deterministic/template match, complete acceptance criteria, strong citations, low-risk table scope.
- Medium (`0.60-0.85`): clear requirement but some generated script/config logic requires careful review.
- Low (`<0.60`): ambiguous, weak citations, missing metadata, or unsupported story type; route to manual handling.

**Story Type Allowlist (Initial)**
- Label/help-text/content-only changes.
- Simple notification text/template changes.
- Simple UI policy or client-script candidates with clear acceptance criteria.
- Dictionary metadata candidates only when explicitly approved for the customer.

**Default Rejection Conditions**
- ACLs, roles, groups, authentication, encryption, integrations, data migration, transform maps, scheduled jobs, or destructive deletes.
- Ambiguous acceptance criteria.
- Missing source citations.
- Model/provider not approved for the story data class.

---

### 8. Prompt Strategy

Prompts must be versioned, task-specific, and constrained by schema.

Prompt inputs:
- minimal story fields
- retrieved context with citations
- customer allowlists and rejection rules
- strict output schema
- examples for the specific story type only

Prompt instructions:
- do not invent fields, tables, sys_ids, policies, or requirements
- do not create destructive changes
- state assumptions explicitly
- return `manual_review` when context is insufficient
- include test suggestions and rollback notes

---

### 9. Non-Functional Requirements

- **Safety**: Dry-run by default. No live mutation in MVP.
- **Compliance**: Provider, storage, logging, and deployment choices must match the customer authorization boundary.
- **Auditability**: Every candidate logs source hashes, retrieval citations, model/provider, prompt version, artifact hash, and reviewer decision.
- **Security**: Least-privilege ServiceNow access, secret manager integration, encryption in transit and at rest, no secrets in prompts or logs.
- **Efficiency**: Deterministic rules first, retrieval caching, prompt minimization, batch analysis, single-story artifact generation.
- **Reliability**: Schema validation, allowlist validation, safety checks, graceful fallback to manual review.
- **Scalability**: Handle 100+ stories per run without requiring 100+ full-context model calls.
- **Extensibility**: Add new story-type handlers without weakening compliance gates.

---

### 10. Engineering Operating Rules

- **Tests first, always**: No production code is written before a failing test proves the intended behavior.
- **Coverage gate**: 90% test coverage is mandatory for the project and for touched core modules. Coverage does not replace meaningful assertions.
- **No hacks**: Temporary shortcuts, hidden bypasses, weak abstractions, or compliance exceptions are not acceptable. If a design is wrong, re-engineer it.
- **Challenge assumptions**: Every sprint must explicitly identify risky assumptions and either validate, reject, or defer them with a named owner.
- **Karpathy-style development discipline**: Keep the system simple, inspect data and failures directly, build tight feedback loops, prefer measurable behavior over cleverness, and avoid premature agentic complexity.
- **Small, testable units**: Each module should have a single clear responsibility, typed boundaries, and focused tests.
- **Security by construction**: Secrets, regulated data, and authorization controls are part of the design, not cleanup work.
- **Definition of done**: Code reviewed, tests passing, coverage gate met, safety/compliance checks passing, assumptions documented, and user-facing behavior verified.

---

### 11. Success Metrics

- Percentage of candidate stories safely classified without model calls.
- Percentage of low-risk stories producing reviewable candidates.
- Reviewer approval rate by story type.
- Reviewer rejection reasons by category.
- Average time saved per approved candidate.
- Retrieval citation coverage.
- Model cost and latency per generated candidate.
- Zero unauthorized model calls, data-boundary violations, or live-instance mutations.

---

### 12. Roadmap

**Phase 1: Regulated MVP**
- Mock data and schema-validated pipeline.
- Rules-first classification.
- Provider policy registry.
- Specialized RAG interfaces with mock/local indexes.
- JSON `UpdateSetCandidate` artifacts.
- Safety gates, allowlists, audit metadata, and reviewer notes.

**Phase 2: Approved Integrations**
- Real ServiceNow Table API ingestion with least-privilege access.
- Approved model endpoint integration.
- Approved vector/retrieval storage.
- Expanded template library.
- Controlled XML candidate generation.

**Phase 3: Review Console**
- Minimal web review workflow.
- Approve/reject feedback capture.
- Metrics dashboard for efficiency, quality, and compliance.
- Export workflow to approved development/sandbox instance.

**Phase 4: Advanced Automation**
- Dependency graph analysis.
- Multi-step agentic workflows only after approval rates, rejection analysis, and compliance controls prove the simpler system is reliable.

---

### 13. Open Decisions

- Target Federal boundary: ServiceNow GCC/FedRAMP High, FedRAMP Moderate, DoD IL4/IL5, contractor CUI, or other.
- Approved model providers and embedding providers for the target boundary.
- Approved vector store and retention policy.
- Customer-specific story type, table, and operation allowlists.
- Whether Now Assist is available and sufficient for the target environment and tasks.
- Whether generated XML is allowed in MVP or deferred until after JSON candidate review proves reliable.

---

This manifest intentionally optimizes for regulated delivery: narrow automation, strong review gates, explicit model governance, specialized retrieval, and measurable efficiency before agentic ambition.
