# ServiceNow Surface Investigator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a general ServiceNow surface investigation layer that retrieves relevant live instance context before model generation and blocks model calls when required context is insufficient.

**Architecture:** Add typed surface context models and retrieval workers in `instance_discovery.py`, wire them into model fulfillment before implementation packet creation, persist the investigation bundle as a DB-backed artifact, and gate provider invocation through existing context escalation controls. Keep public documentation retrieval behind the existing RAG boundary for now.

**Tech Stack:** Python, Pydantic, FastAPI runtime worker, ServiceNow Table API client, pytest, ruff, mypy.

---

### Task 1: Surface Context Models And Retrieval

**Files:**
- Modify: `src/jedi_devproject/instance_discovery.py`
- Test: `tests/test_instance_discovery.py`

- [ ] **Step 1: Write failing tests**

Add tests proving a surface bundle includes dictionary/form context plus Business Rule, Client Script, UI Policy, Flow, Script Include, integration, CMDB/discovery, and public docs placeholders.

- [ ] **Step 2: Verify tests fail**

Run: `python3 -m pytest tests/test_instance_discovery.py -q`

- [ ] **Step 3: Implement minimal models and retrieval**

Add `ServiceNowSurfaceContext`, `ServiceNowSurfaceContextBundle`, `plan_surface_investigation()`, and `discover_servicenow_surface_context()`.

- [ ] **Step 4: Verify tests pass**

Run: `python3 -m pytest tests/test_instance_discovery.py -q`

### Task 2: Packet Context Sufficiency Gate

**Files:**
- Modify: `src/jedi_devproject/implementation_packet.py`
- Test: `tests/test_implementation_packet.py`

- [ ] **Step 1: Write failing tests**

Add tests proving implementation packets include the surface bundle and report insufficient context when required surfaces are missing.

- [ ] **Step 2: Verify tests fail**

Run: `python3 -m pytest tests/test_implementation_packet.py -q`

- [ ] **Step 3: Implement minimal packet wiring**

Add optional `surface_context_bundle` input and include it in model payload and sufficiency scoring.

- [ ] **Step 4: Verify tests pass**

Run: `python3 -m pytest tests/test_implementation_packet.py -q`

### Task 3: Runtime Artifact And Model Call Guard

**Files:**
- Modify: `src/jedi_devproject/model_fulfillment.py`
- Test: `tests/test_model_fulfillment.py`

- [ ] **Step 1: Write failing tests**

Add tests proving the worker persists an `instance_context_bundle` artifact and does not call the provider when context is insufficient.

- [ ] **Step 2: Verify tests fail**

Run: `python3 -m pytest tests/test_model_fulfillment.py -q`

- [ ] **Step 3: Implement minimal runtime wiring**

Retrieve the bundle, build the packet with it, return a manual-review candidate without provider invocation when context escalation blocks the model, and include the context artifact in fulfillment artifacts.

- [ ] **Step 4: Verify tests pass**

Run: `python3 -m pytest tests/test_model_fulfillment.py -q`

### Task 4: Docs And Quality Gate

**Files:**
- Create: `docs/sprints/sprint-106-change-log.md`
- Modify: `docs/operator-guide.md`
- Modify: `tests/test_project_docs.py`

- [ ] **Step 1: Add docs tests**

Assert the operator guide and sprint log document broad ServiceNow surface investigation and fail-closed model gating.

- [ ] **Step 2: Implement docs**

Document supported retrieval surfaces, artifact behavior, public docs RAG boundary, and no-guessing model gate.

- [ ] **Step 3: Run full gate**

Run: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90`
