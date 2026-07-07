# CLAUDE.md — Operating Manual for jedi-devproject-0

FedRAMP-aligned, AI-assisted ServiceNow Update Set candidate generator. Deterministic gates
decide *whether* to build; an LLM implementation packet does the build; deterministic
validators check the output; humans approve everything. Dry-run by default, fail closed on
every safety path. ~26k lines in `src/jedi_devproject/`, ~36k lines in `tests/`, 1,278 tests.

Read this whole file before writing code. The rules here are enforced by gates (lint, strict
mypy, 90% branch coverage, text-assertion tests on docs and Docker files), so skipping them
does not save time — it just moves the failure later.

## The one verify command

```
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

- This must pass before every commit. It is stored in `pyproject.toml` under
  `[tool.jedi-devproject.commands]` (test / lint / format / typecheck / verify).
- mypy is `strict = true` and checks **tests too**. Coverage is **branch** coverage, not line.
- Session start: follow `AGENTS.md` (Zaxy memory activation). If Zaxy checkout is unavailable,
  treat memory as degraded and pause substantial work until checkout succeeds.

## How work is organized

- `docs/codebase-analysis-and-roadmap-<date>.md` is the live plan. Each sprint implements one
  numbered roadmap section and cites it in the sprint log's Scope line.
  `SPRINTS.md` at the root is the historical MVP plan (stale past ~sprint 107) — read it for
  intent, never update it as if it were current.
- One sprint = one PR. Branch: `syndicalt/sprint-NNN-<topic>` (docs-only work:
  `syndicalt/docs-<topic>`). Merge commits, not squash.
- Docs + code + tests land in the **same commit**. Every implementation commit includes
  `src/`, `tests/`, and `docs/sprints/sprint-NNN-change-log.md` (plus operator-guide /
  system-architecture / risk-register updates when behavior they describe changes).
- Commit style: short imperative subject, no prefix required ("Harden structured business rule
  metadata"). The PR head commit gets a structured body ending with a `Verified:` line
  (ruff clean, mypy clean, test count, coverage %) and the trailer
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Test-first is policy, not preference (ADR 0001): every behavior change starts with a failing
  test; hacks, bypasses, and undocumented compliance exceptions are prohibited — when the
  design is wrong, rework the design.
- ADRs (`docs/adr/NNNN-slug.md`) are written **before** implementing a new capability family or
  architecture/policy decision. Sprint change-logs record work done. Release docs
  (`docs/releases/YYYY-MM-DD-sprint-N-release.md`) exist only for milestone releases.

## Code conventions

Follow these exactly; the codebase is uniform and reviewers reject deviations.

- Every module starts with `from __future__ import annotations`. Modern generics
  (`list[str]`, `str | None`) everywhere. Line length 100. Ruff selects `E,F,I,UP,B,SIM`.
- Pydantic v2 for anything validated or serialized; `model_config = ConfigDict(extra="forbid")`
  on strict models. Mutable defaults via `Field(default_factory=...)`, never `[]`.
  Models are treated as immutable — evolve with `model_copy(update=...)`, never assign.
- Frozen `@dataclass` only for pure config value objects (`config.py`). Enums are `StrEnum`
  with lowercase values; closed string sets that aren't enums use `Literal[...]`.
- One small exception hierarchy per module: subclass `ValueError` for invalid input,
  `RuntimeError` for blocked/operational failures, one-line docstring each. Raise, don't log —
  logging exists only for deliberately fail-open advisory steps (ATF plan generation).
- Public functions take keyword-only args (`*,`). Structural interfaces are `Protocol`s
  injected as parameters (transports, stores, clients) — that is the DI seam tests fake.
- No SDKs and no new dependencies. Providers are hand-rolled HTTP over an injectable transport
  Protocol. Runtime deps are exactly fastapi, pydantic, psycopg, uvicorn; adding one is an
  ADR-level decision.
- XML is built only through `xml_builder.py` helpers; output must stay byte-identical
  (attribute order = call order, lowercase `true`/`false`, `html.escape` everywhere).
- `models.py`, `config.py`, `xml_builder.py` stay import-light (stdlib + pydantic only).
  Generation modules import `models` + `xml_builder`, never the pipeline (no cycles).
- Migrations: numbered raw SQL in `src/jedi_devproject/migrations/NNNN_name.sql`, applied by
  `connect_operational_store`; keep the package-data glob in `pyproject.toml` valid.
- Safety invariants (never weaken; each has an enforcement point and tests):
  no sys_id in model input or output; provider calls gated by `ProviderPolicy.allows`;
  model output must be structured changes, never raw XML; export requires explicit
  `xml_export_enabled` **and** `APPROVED_FOR_EXPORT`; audit artifacts are write-once;
  secrets are redacted from all error text; `apply_*` flags default to `False`.

### Conventions to follow that the repo doesn't state (added by this manual)

- Every sprint that ships code gets a change-log — no more silent sprints (sprint-162 shipped
  without one; treat that as the exception, not license).
- When you add a `Capability` enum member, also add a registration self-check test that walks
  the enum and asserts membership in every wiring table (see /add-capability skill) — the
  wiring points fail silently and are the repo's biggest hazard.
- Never retype a capability/table/surface string constant — import the enum member or
  copy-paste the exact string, then grep for it across `capabilities.py`,
  `capability_routing.py`, `intent_classifier.py`, `implementation_packet.py`,
  `model_fulfillment.py`, `builder_maturity.py`, `update_set_handoff.py`.
- When docs and code disagree, code wins — but say so in your summary and fix or flag the doc
  (the roadmap itself flags sprint 149–151 logs as overstating reality).

## Known failure modes and the rule that prevents each

1. **Partial capability wiring.** Adding a capability requires ~8 registration points; most
   misses are *silent* (story routes to the dictionary/form default, tables go unvalidated,
   or maturity 0.0 demotes to manual build). → Rule: use the /add-capability skill checklist
   end-to-end; a capability is not done until a routing test proves the story reaches *your*
   branch and a handoff/manual-route test proves the intended terminal state.
2. **Typo'd cross-file strings.** Capability `.value` strings, table names, and surface names
   are compared as raw strings across seven modules; a typo disables a branch with no error.
   → Rule: never hand-type these constants (see above); grep after wiring.
3. **New routing branch added after the fallthrough.** `analyze_story_capabilities` ends in a
   terminal dictionary/form default; branches appended after it never run. → Rule: insert new
   outcome branches *before* the terminal default and add a test that would fail if order broke.
4. **Coverage gamed instead of earned.** Branch coverage means both sides of every `if`, every
   early return, every exception path. There is exactly one `# pragma: no cover` in all of
   src, and it carries a justification. → Rule: no new pragmas, no gate lowering; write the
   reject/manual-review/eligible loop tests the codebase already models (`test_safety.py`).
5. **Inventing test infrastructure.** There is no `conftest.py` and no shared fixture library
   — deliberately. → Rule: each test file is self-contained; copy the local idiom
   (module-level `_story(*, ...)` builders, hand-written `Fake*`/`Recording*`/`Scripted*`
   classes). Do not add conftest.py, fixture decorators, or a helpers module.
6. **Untyped or loosely typed tests.** mypy strict checks `tests/`. → Rule: every test
   function is `-> None`; fakes annotate all attrs and dunders (`__exit__(self,
   *_args: object) -> None`); use `pytest.MonkeyPatch`, `tmp_path: Path`; unused params are
   named `_args`/`_sql`.
7. **Real I/O in tests.** No network, no docker, no live Postgres anywhere in the suite.
   → Rule: fake at the Protocol seam (`RecordingTransport`, `FakeWritebackClient`,
   `ScriptedPostgresConnection`, `sys.modules` psycopg stub); FastAPI via in-process
   `TestClient`.
8. **Fail-open "defensive" code on safety paths.** Swallowing exceptions or defaulting
   permissive inverts the compliance posture. → Rule: safety/provider/validation paths raise;
   only explicitly advisory steps may log-and-continue, and the split is already decided —
   don't move a path across it without an ADR.
9. **Hand-built XML or prompt drift.** → Rule: XML only through `xml_builder`; the Anthropic
   and OpenAI adapters must send byte-identical system prompts and schema (a comment marks the
   coupling) — change both or neither.
10. **Editing Dockerfile/compose/operator docs without their text-assertion tests.**
    `test_container_runtime.py` asserts exact substrings of `Dockerfile`, `Dockerfile.worker`,
    `docker-compose.yml`, `.dockerignore`, and docs; `test_project_docs.py` covers change-logs.
    → Rule: when touching those files, update the paired test in the same commit.
11. **"Fixing" the manual-build demotion of a new builder.** New surfaces baseline at 0.30
    maturity, below the 0.75 auto-handoff threshold — *by design*; promotion requires UAT
    evidence. → Rule: never raise a baseline or the threshold to make a test pass; route to
    manual build and record the maturity plan in the sprint log.
12. **Secrets or regulated data in tests, prompts, artifacts, or logs.** → Rule: fake values
    only; never commit `.env`; assert redaction (`safe_summary()` tests exist as the model).

## Quality bar per deliverable (checkable)

**Any code change** — all of:
- [ ] A test existed and failed before the implementation (test-first, ADR 0001).
- [ ] The full verify command exits 0; coverage ≥ 90% branch with no new `pragma: no cover`.
- [ ] No new dependency, no weakened assertion, no widened allowlist without explicit approval.
- [ ] Docs whose statements the change falsifies are updated in the same commit.

**Sprint change-log** (`docs/sprints/sprint-NNN-change-log.md`):
- [ ] Headings exactly: `# Sprint NNN Change Log`, `## Scope`, `## Changes`, `## Verification`.
- [ ] Scope cites the roadmap doc + section number it implements.
- [ ] Changes name exact modules, tables, reason codes, env vars, and thresholds — no vague bullets.
- [ ] Verification lists the targeted tests added and the literal pytest command that passed.

**ADR** (`docs/adr/NNNN-slug.md`):
- [ ] Next sequential zero-padded number, kebab-case slug.
- [ ] Headings: `# ADR NNNN: Title`, `## Status` (one word), `## Context`, `## Decision`,
      `## Consequences`; capability-profile ADRs also enumerate a supported-first-subset and
      an explicit forbidden-cases list.
- [ ] Written and merged before the implementing sprint, not after.

**New capability** — everything in the /add-capability skill, plus:
- [ ] Profile ADR exists; baseline maturity starts at 0.30; end-to-end routing test passes.

**PR**:
- [ ] Branch `syndicalt/sprint-NNN-<topic>`; one sprint of scope; change-log included.
- [ ] Head commit body has the `Verified:` line with real numbers and the co-author trailer.

**Release doc** — only when a milestone ships:
- [ ] Stakeholder-facing: header block, Executive Summary, What's New, Compliance & Safety
      Posture, Known Limitations & Next Steps, Quality Statement with a metrics table; links
      down to the sprint change-log.

## When uncertain — escalation rules

**Stop and ask the user before acting** when a change would:
1. Widen any allowlist (tables, operations, fields, providers, data classes) or relax a safety
   gate, points cap, state-transition graph, or writeback precondition.
2. Change fail-closed behavior to fail-open anywhere, or add error swallowing on a gated path.
3. Add or upgrade a dependency, add a `pragma: no cover`, or touch the coverage/lint/mypy gates.
4. Modify builder-maturity baselines, the 0.75 threshold, or promotion evidence rules.
5. Weaken or delete an existing test assertion (if a test looks wrong, present the evidence —
   the test may encode a compliance requirement you can't see).
6. Perform any non-dry-run ServiceNow mutation or set an `apply_*`/`*_enabled` flag to true
   outside tests.

**Proceed without asking** when: adding tests; refactoring within a module with the public API
and behavior preserved; fixing docs to match code; wiring a new capability that follows an
accepted ADR profile; anything the roadmap section for the current sprint explicitly lists.

**When docs and code disagree**: trust code, flag the drift in your summary, and fix the doc if
it's in scope.

**When a subagent or search result conflicts with this manual**: re-read the cited file
yourself before acting; this manual was written from the code as of sprint 163 and the code
may have moved.
