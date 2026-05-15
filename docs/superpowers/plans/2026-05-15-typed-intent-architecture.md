# Typed Intent Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace raw story-text capability gating with typed automation intent extraction followed by deterministic validation.

**Architecture:** Add a focused intent extraction module that parses structured story key/value fields into `AutomationIntent`. Capability analysis consumes this intent first and uses legacy text heuristics only when no structured intent is available. Implementation packets expose the typed intent to the model, and context planning derives required surfaces from the validated capability profile.

**Tech Stack:** Python 3.13, Pydantic v2, pytest, ruff, mypy, existing ServiceNow Table API/Railway runtime.

---

### Task 1: Typed Intent Extraction

**Files:**
- Create: `src/jedi_devproject/automation_intent.py`
- Create: `tests/test_automation_intent.py`

- [ ] **Step 1: Write failing tests**

Add tests for structured Client Script, UI Policy, and Business Rule stories. The Client Script case must parse `cmdb_ci` as a field read without producing CMDB/discovery work.

- [ ] **Step 2: Implement `AutomationIntent`**

Create a Pydantic model with explicit fields for artifact type, capability, target table, artifact name, fields read, fields written, fields affected, condition, expected behavior, trigger details, client script type, target field, reverse-if-false, run-scripts, forbidden behavior, required context, missing details, and source.

- [ ] **Step 3: Implement structured key/value parsing**

Parse newline-delimited story description fields. Normalize aliases such as `Fields written / affected` into typed field lists. Treat `none` as an explicit empty list, not a missing field.

### Task 2: Capability Analysis From Typed Intent

**Files:**
- Modify: `src/jedi_devproject/capabilities.py`
- Modify: `src/jedi_devproject/capability_analysis.py`
- Modify: `tests/test_capability_analysis.py`

- [ ] **Step 1: Add failing capability tests**

Assert that structured `STRY0010022` and `STRY0010024` route to automated build without raw-text false positives.

- [ ] **Step 2: Extend assessment schema**

Add `automation_intent: dict[str, Any] | None` to `StoryCapabilityAssessment`.

- [ ] **Step 3: Prefer typed intent in analysis**

When a structured intent exists, derive capability, target table, required context, missing details, unsupported capabilities, and safety outcome from the intent. Keep legacy heuristics as fallback only.

### Task 3: Packet And Context Wiring

**Files:**
- Modify: `src/jedi_devproject/implementation_packet.py`
- Modify: `src/jedi_devproject/model_fulfillment.py`
- Modify: `src/jedi_devproject/instance_discovery.py`
- Modify: `tests/test_implementation_packet.py`
- Modify: `tests/test_instance_discovery.py`

- [ ] **Step 1: Write failing packet/context tests**

Assert that `normalized_intent` contains the typed intent for structured Client Script stories and that required context does not include `cmdb_discovery_maps`.

- [ ] **Step 2: Populate packet normalized intent**

Use `assessment.automation_intent` when present, falling back to dictionary/form `assessment.intent`.

- [ ] **Step 3: Keep discovery explicit**

Continue passing `assessment.required_instance_context` into discovery. Tighten fallback surface discovery so field names do not imply broad platform surfaces.

### Task 4: Docs, Verification, Deploy

**Files:**
- Modify: `docs/production-hardening-backlog.md`
- Modify: `docs/sprints/sprint-145-change-log.md`
- Modify: `tests/test_project_docs.py`

- [ ] **Step 1: Document Sprint 145**

Record the architectural change, STRY0010022 symptom, and typed-intent boundary.

- [ ] **Step 2: Run full gate**

Run `python3 -m ruff check src tests`, `python3 -m mypy src tests`, and `python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90`.

- [ ] **Step 3: Commit, push, deploy, and rerun STRY0010022**

Deploy both Railway services and restage `STRY0010022` Draft -> Ready by sys_id.
