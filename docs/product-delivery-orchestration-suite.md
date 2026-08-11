# Product Delivery Orchestration Suite

## Purpose

This document sketches the target data flow for expanding JEDI from a ServiceNow
story fulfillment sidecar into a full product-delivery orchestration suite. The
suite should take work from initial customer contact through structured intake,
solution design, implementation, validation, controlled release, and customer
acceptance.

ServiceNow remains the primary business work surface and system of record for
regulated delivery. The orchestration suite provides the agent runtime, context
dossier, durable artifacts, evidence trail, model gateway, and automation
handoffs around that work surface.

## End-To-End Flow

```mermaid
flowchart TB
    %% Intake
    subgraph Intake["1. Initial Customer Contact And Intake"]
        Contact["Customer contact\nmeeting, email, chat, RFP, SOW"]
        Transcript["Transcript and source documents"]
        SNIntake["ServiceNow demand, idea,\nepic, story, or case"]
        IntakeNorm["Intake normalization\ncustomer, problem, scope, actors"]
        Classification["Data classification\npublic, internal, CUI, sensitive"]
        Contact --> Transcript
        Contact --> SNIntake
        Transcript --> IntakeNorm
        SNIntake --> IntakeNorm
        IntakeNorm --> Classification
    end

    %% Context
    subgraph Context["2. Context Dossier Builder"]
        CustomerCtx["Customer context\naccounts, contracts, prior work"]
        PlatformCtx["ServiceNow live context\ntables, forms, flows, scripts, catalog, CMDB"]
        KnowledgeCtx["Knowledge context\ninternal docs, prior artifacts, public docs"]
        PolicyCtx["Policy context\nFedRAMP, NIST, security, data rules"]
        Dossier["Context dossier\nstructured, cited, minimized"]
        CustomerCtx --> Dossier
        PlatformCtx --> Dossier
        KnowledgeCtx --> Dossier
        PolicyCtx --> Dossier
    end

    Classification --> Dossier

    %% Orchestration
    subgraph Orchestration["3. Supervisor / Router Agent"]
        Router["Supervisor router\nMoE gate, decomposition, dynamic routing"]
        Plan["Delivery plan\nphases, owners, dependencies"]
        State["Orchestration state\njobs, attempts, approvals, blockers"]
        Router --> Plan
        Router --> State
    end

    Dossier --> Router

    %% Agents
    subgraph Agents["4. Specialist Agent Workbenches"]
        Req["Requirements Analyst Agent\nrequirement contract, acceptance criteria,\nambiguity and rewrite feedback"]
        Arch["Solution Architect Agent\nsolution blueprint, platform surface map,\ndependencies, risk"]
        Config["Implementation Configurator Agent\nimplementation packet, candidate changes,\nretrieved update set or code artifact"]
        QA["Tester / QA Agent\ntest plan, automated checks,\nUAT checklist, defect evidence"]
        Integrator["Integrator Agent\nAPI design, data mapping,\ncredential and endpoint requirements"]
        DevOps["Deployment / DevOps Agent\ndeployment manifest, change request,\nrelease and rollback plan"]
        Docs["Documentation / Knowledge Agent\nadmin docs, user docs,\nKB articles, release notes"]
        Sec["Compliance / Security Agent\ncontrol mapping, threat review,\naudit evidence, exception handling"]
    end

    Router --> Req
    Router --> Arch
    Router --> Config
    Router --> QA
    Router --> Integrator
    Router --> DevOps
    Router --> Docs
    Router --> Sec

    Req --> Router
    Arch --> Router
    Config --> Router
    QA --> Router
    Integrator --> Router
    DevOps --> Router
    Docs --> Router
    Sec --> Router

    %% Gates
    subgraph Gates["5. Human And Policy Gates"]
        IntakeGate{"Intake complete?"}
        ScopeGate{"Scope approved?"}
        ArchGate{"Architecture approved?"}
        SecGate{"Security and data policy approved?"}
        AutoGate{"Automation confidence sufficient?"}
        TestGate{"Test and UAT evidence accepted?"}
        ReleaseGate{"Change and release approved?"}
        AcceptGate{"Customer accepts delivery?"}
    end

    Plan --> IntakeGate
    IntakeGate --> ScopeGate
    ScopeGate --> ArchGate
    ArchGate --> SecGate
    SecGate --> AutoGate
    AutoGate --> TestGate
    TestGate --> ReleaseGate
    ReleaseGate --> AcceptGate

    %% Stores
    subgraph Stores["6. Durable System Stores"]
        PG[("PostgreSQL operational store\nlifecycle events, jobs, artifacts, audit")]
        ArtifactStore[("Artifact store\npackets, candidates, evidence, manifests")]
        VectorStore[("Retrieval indexes\ncontext chunks, citations, examples")]
        Secrets["Secrets manager\nOAuth, API keys, signing secrets"]
        ModelGateway["Model gateway\napproved providers, schemas, logging policy"]
        AdminConsole["Admin console\njobs, errors, replay, config, observability"]
    end

    State --> PG
    Req --> ArtifactStore
    Arch --> ArtifactStore
    Config --> ArtifactStore
    QA --> ArtifactStore
    Integrator --> ArtifactStore
    DevOps --> ArtifactStore
    Docs --> ArtifactStore
    Sec --> ArtifactStore
    Dossier --> VectorStore
    Router --> ModelGateway
    Router --> Secrets
    PG --> AdminConsole
    ArtifactStore --> AdminConsole

    %% ServiceNow delivery surface
    subgraph ServiceNow["7. ServiceNow Business Work Surface"]
        Demand["Demand / idea / epic"]
        Story["Story / task"]
        WorkNotes["Work notes and AI status"]
        UpdateSet["Retrieved update set\npreview, scan, commit"]
        Change["Change request"]
        UAT["UAT signoff"]
        Complete["Complete state"]
    end

    SNIntake --> Demand
    Demand --> Story
    Router --> WorkNotes
    Config --> UpdateSet
    DevOps --> Change
    QA --> UAT
    AcceptGate --> Complete

    %% Delivery
    subgraph Delivery["8. Product Delivery And Feedback"]
        Release["Production release"]
        Handoff["Customer handoff\ntraining, docs, release notes"]
        Hypercare["Hypercare\nmonitoring, defects, adoption"]
        Lessons["Lessons learned\nreusable patterns, new examples"]
    end

    Complete --> Release
    Release --> Handoff
    Handoff --> Hypercare
    Hypercare --> Lessons
    Lessons --> KnowledgeCtx
    Lessons --> VectorStore
```

## Artifact Lifecycle

Every agent should emit structured artifacts. Prose summaries are useful for
humans, but downstream automation should depend on typed contracts.

```mermaid
flowchart LR
    Intake["Raw intake\ntranscripts, docs, ServiceNow records"]
    ReqContract["RequirementContract\nproblem, actors, outcomes,\nacceptance criteria"]
    Blueprint["SolutionBlueprint\nsurfaces, design, dependencies,\nrisk, open questions"]
    Packet["ImplementationPacket\ncontext dossier, allowed changes,\nvalidation contract"]
    Candidate["CandidateChange\nstructured model or deterministic output"]
    Handoff["DeliveryHandoff\nretrieved update set, code artifact,\nconfig artifact, or manual plan"]
    TestEvidence["TestEvidencePackage\nunit, integration, UAT,\ndefects, screenshots"]
    Compliance["ControlAssessment\npolicy mapping, approvals,\nexceptions, audit links"]
    Manifest["DeliveryManifest\nrelease contents, rollback,\ndocs, support owner"]

    Intake --> ReqContract
    ReqContract --> Blueprint
    Blueprint --> Packet
    Packet --> Candidate
    Candidate --> Handoff
    Handoff --> TestEvidence
    TestEvidence --> Compliance
    Compliance --> Manifest
```

## Build Implications

- The supervisor/router coordinates work but should not be the durable system of
  record.
- Each agent boundary needs a typed input and output contract before it becomes
  production automation.
- ServiceNow lifecycle events should continue to drive the regulated business
  workflow.
- The orchestration suite should write useful feedback to the story whenever
  automation cannot proceed, including suggested rewrites when the work can be
  made automatable.
- Deterministic builders remain preferred for mature ServiceNow surfaces.
- LLM-generated candidates should be allowed only when the context dossier,
  policy gate, and validator can explain why the handoff is safe enough for
  human preview.
- Human review remains explicit at architecture approval, security approval,
  retrieved update set preview and commit, UAT, change approval, and final
  customer acceptance.
