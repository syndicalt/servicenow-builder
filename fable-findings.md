# Fable Findings — Codebase Assessment

**Date**: 2026-07-06
**Assessed by**: Claude Fable 5, after a full read of the codebase (src ~26k lines, tests ~36k lines, docs, git history through sprint 163), with direct reads of the hot paths (`capability_routing.py`, `implementation_packet.py`, `business_rule_generation.py`, representative test files).

## Ratings

| Criterion | Score |
|---|---|
| 1. Project architecture & code quality | **8/10** |
| 2. Runtime efficiency & code economy | **7/10** |
| 3. AI slop (10 = slop-free) | **7/10** |

---

## 1. Architecture & code quality: 8/10

The strengths are real and rare: clean layering (models → gates → routing → packet → handoff, with `models.py`/`xml_builder.py` kept import-light), Protocol-based DI seams that make the entire 1,278-test suite runnable with zero I/O, fail-closed safety enforced at code level rather than by convention, mypy strict across src *and* tests, one uniform idiom throughout, and ADR-driven design that the code actually follows. Zero TODOs/FIXMEs/HACKs in the tree, one justified pragma. Most codebases claiming this discipline don't have it; this one does.

**What keeps it from 9–10:**

- **`implementation_packet.py` is a 1,746-line, 50-function god-module.** It builds packets, calls providers, validates output, reconciles, scores maturity, and routes. It's the module every capability touches and the one a change is most likely to break. Splitting validation, reconciliation, and routing would be the single highest-leverage refactor.
- **The capability wiring has no single source of truth.** ~8 hand-maintained registration points (registry, a separately-maintained profile list, supported set, expected-tables map, surface groups, intent keywords, routing branch, handoff dispatch) keyed by raw strings, where most misses fail *silently*. A registration self-test or a declarative profile that derives the other tables would convert this from the repo's biggest hazard into a non-issue.
- **`dict[str, Any]` context bags** (`additional_context`, `automation_intent` payloads) accessed with `.get()` + `isinstance` guards — the alias-tolerant `or`-chains in `_business_rule_intent` (`business_rule_generation.py:83-113`) exist because upstream payloads are schemaless. Typed packets would delete a whole class of defensive code.
- **Order-sensitive routing fallthrough** in `analyze_story_capabilities` — correctness depends on branch position relative to the terminal dictionary/form default, which nothing structural enforces.

## 2. Runtime efficiency & code economy: 7/10

Runtime efficiency alone would be ~9: this is an I/O-bound orchestration app and it's built like one. Deterministic classifiers and gates run *before* any model call (the expensive resource), retrieval is cached by source hash + prompt version, sprint 162 added dedup/caching/retention explicitly, the worker claims jobs with `SELECT … FOR UPDATE SKIP LOCKED`, and XML is flat string-building. Nothing hot, nothing quadratic, no gratuitous allocation. There's little to optimize because the design spends model tokens, not CPU.

**Code economy is what drags the score:**

- **Routing boilerplate**: `analyze_story_capabilities` is ~10 consecutive copies of the same 12-argument `return _assessment(...)` block differing in one predicate and one reason string (`capability_routing.py:151-330`). A `(predicate, outcome, reasons)` table would cut ~200 lines and make branch order explicit.
- **Near-clone generation modules**: eleven `*_generation.py` files share the same intent-model → validate → payload → customer-update shape with no shared skeleton.
- **Deliberate but expensive test duplication**: 36k lines of tests, with `_story()` builders and `Fake*` classes re-declared per file (no conftest by design). It buys isolation, but the suite is ~40% larger than it needs to be, and every model-schema change fans out across dozens of files.
- **Copy-paste-coupled provider adapters**: Anthropic and OpenAI must send byte-identical prompts/schema, enforced only by a comment.

## 3. AI slop: 7/10 (10 = slop-free)

For a codebase with `Co-Authored-By: Claude` on essentially every commit, this is remarkably clean — worth saying because it's uncommon. The classic slop markers are absent: no narrating comments, no dead code, no defensive try/except blankets, no invented abstractions, no README inflation. The comments that exist state non-obvious constraints (the free-text-catalog routing comment at `capability_routing.py:187-189` is exactly right). The docs even flag their own drift honestly.

**What keeps it from 9–10 — the fingerprints are structural rather than cosmetic:**

- **Volume-as-diligence**: the repetitive 12-arg return blocks, the alias soup (`fields.get("script") or fields.get("action_script") or fields.get("script_body")`), and eleven parallel generation modules read like a model satisfying gates by producing more uniform code rather than compressing the design. A human at this quality level would have factored these by now.
- **Ritualized tests**: `test_container_runtime.py` asserting exact substrings of Dockerfiles and docs, and change-logs being "covered by `test_project_docs.py`", are test-first ceremony applied where it has low information value — tests that pass because the file was pasted into both places.
- **Formulaic doc mass**: 164 sprint change-logs in identical template prose, plus a stale 22k-character `SPRINTS.md`, is documentation whose marginal entry costs nothing to generate and therefore accumulates; the roadmap doc itself concedes some logs overstated what shipped (sprint 149–151).
- **Keyword-string intent classification** (`_requested_capabilities`, forbidden-detail regexes) is brittle NLP-by-substring — defensible as a deterministic gate, but the sheer number of hand-tuned phrase lists suggests accretion over design.

## Summary

The *safety architecture and discipline* are 9-tier; the *economy* is where a skeptical senior reviewer would push back. Both lower scores trace to the same root: uniform expansion was always cheaper than consolidation, and nothing in the gates ever forced consolidation.

**Highest-leverage fixes, in order:**
1. Registration self-test walking the `Capability` enum across every wiring table (kills the silent-failure class; cheap).
2. Split `implementation_packet.py` into packet-build / validation / maturity-routing modules.
3. Table-drive the routing branches in `analyze_story_capabilities`.
4. Typed schema for `additional_context` / `automation_intent` payloads.
5. Shared skeleton (or shared prompt/schema constant) for the two provider adapters.

---

## Sprint 164 dispositions (2026-07-06)

All five highest-leverage fixes were implemented in sprint 164
(`docs/sprints/sprint-164-change-log.md`), behavior-preserving, with byte-identity evidence
and the full gate green (ruff clean, mypy --strict clean, 1,298 tests, coverage 93.77%).

**Fixed:**
1. Registration self-test — `tests/test_capability_registration.py`: ten ledger tests over
   every wiring table, with documented exemption ledgers for the deliberate irregularities
   (`field_label_create` profile-less family alias, `flow_modify` structured-intent-only,
   surface-unmapped code-generation tables scoring the 0.0 manual-review default).
2. God-module split — `implementation_packet.py` 1,746 → 604 lines plus `packet_model.py`,
   `packet_context.py`, `packet_validation.py`, `packet_intent_changes.py`; acyclic DAG;
   all previous imports preserved via re-exports.
3. Table-driven routing — `capability_routing.py` 762 → 662 lines; free-text and structured
   chains are ordered `(name, matcher)` rule tables; precedence pinned by
   `tests/test_capability_routing_rules.py`.
4. Typed payloads — `parsed_automation_intent()` parse-once boundary reader replaces the
   `isinstance`/`.get`/`cast` chain in `model_fulfillment._required_surfaces_for_assessment`.
5. Shared provider contract — `provider_contract.py` holds the byte-identical prompt and
   schema; both adapters import it; coupling asserted by `tests/test_provider_contract.py`.

**Deliberate design, not fixed (with reasons):**
- Per-file test builders and fakes (no conftest): house convention that buys test isolation;
  codified in CLAUDE.md rather than "fixed".
- Keyword/regex intent classification: the deterministic pre-model gate is a compliance
  feature (ADR 0001 fail-closed posture); replacing it with anything model-driven would
  invert the safety architecture.
- Alias-tolerant `or`-chains in `*_generation.py` intent extractors: each alias is a
  deliberate tolerance for model-output field naming; the chains are the explicit contract.
- Writeback `u_ai_*` `.get()` reads: four single-key reads of genuinely external ServiceNow
  custom fields with None semantics — a typed accessor would add machinery without deleting
  a branch.
- Eleven near-clone `*_generation.py` modules: ADR 0006 mandates separately versioned
  capability profiles; shared helpers already live in `validation_helpers.py`/`xml_builder.py`.
  Further consolidation trades auditability of per-artifact contracts for line count.

**Follow-up (not this sprint):**
- `packet_intent_changes.py` readers still parse `normalized_intent` dicts defensively:
  those payloads are DB-resident (in-flight runtime jobs), so typing them requires a
  versioned packet-schema migration, not a refactor. Candidate for a future sprint with an
  ADR covering payload versioning.
- Sprint change-log formulaicity and `SPRINTS.md` staleness: documentation posture, recorded
  in CLAUDE.md (SPRINTS.md is historical; roadmap doc is the live plan).
