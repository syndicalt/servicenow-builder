# Sprint 164 Change Log

## Scope

Architecture and code-economy hardening pass implementing the highest-leverage fixes from
`fable-findings.md` (2026-07-06 codebase assessment): kill the silent capability-wiring
failure class, split the `implementation_packet.py` god-module, table-drive the routing
branches, extract the shared provider contract, and add a parse-once typed reader for
serialized automation-intent payloads. Zero behavior change: every reason string, outcome,
prompt byte, and schema byte is preserved; verification below includes byte-identity checks
against the pre-refactor tree.

## Changes

- Added `tests/test_capability_registration.py`: ten ledger tests walking the `Capability`
  enum across every separately maintained wiring table (`CAPABILITY_REGISTRY`,
  `generation_capability_profiles()`, `SUPPORTED_BASELINE_CAPABILITIES`,
  `_expected_tables_for_packet`, `CHANGE_TABLE_SURFACE_GROUPS`, `BASELINE_BUILDER_MATURITY`,
  `CODE_SURFACE_MAP`). Documented exemption ledgers pin the deliberate irregularities:
  `field_label_create` rides the dictionary/form family without a standalone profile,
  `flow_modify` is structured-intent-only, `business_rule_generate`/`client_script_generate`/
  `script_include_generate`/`cmdb_ire_generate` change tables are surface-unmapped and score
  the 0.0 unmapped default (manual review by design). A new enum member now fails loudly
  until it is fully wired or consciously exempted.
- Split `implementation_packet.py` (1,746 lines) into a focused family with an acyclic
  dependency graph: `packet_model.py` (packet models, constants, pure compaction helpers,
  273 lines), `packet_context.py` (context dossier/sufficiency/XML-shape references,
  212 lines), `packet_validation.py` (deterministic model-response validation, 117 lines),
  `packet_intent_changes.py` (normalized-intent to deterministic changes builders,
  622 lines), and the slimmed orchestrator `implementation_packet.py` (604 lines) which
  re-exports every previously importable name via `__all__` so no caller changed. Pure code
  motion: moved bodies verified byte-identical against the pre-split module.
- Table-drove `capability_routing.py` (762 to 662 lines): the free-text and structured-intent
  branch chains are now ordered rule tables (`_FREE_TEXT_RULES`, `_STRUCTURED_INTENT_RULES`)
  of named `(rule, matcher)` entries evaluated first-match-wins over a frozen
  `_RoutingContext`, with the terminal dictionary/form fallthrough kept explicit after each
  table. Branch precedence is now visible data; reason strings were copied byte-identically
  (verified programmatically against the pre-refactor code). Added
  `tests/test_capability_routing_rules.py` pinning precedence: points gates beat
  forbidden-detail rules, forbidden-detail rules beat the unsupported gate, and mid-table
  matches never reach the automated-build fallthrough.
- Extracted `provider_contract.py` as the single source of truth for the byte-identical
  system prompt (`IMPLEMENTATION_SYSTEM_PROMPT`) and JSON schema
  (`implementation_candidate_schema()`) both model adapters must send. Replaces the
  copy-paste-coupled prompt in `anthropic_provider.py` and the private cross-module schema
  import from `openai_provider.py`. Added `tests/test_provider_contract.py` asserting both
  adapters transmit the shared constants (Anthropic still wrapped by
  `_without_unsupported_constraints`). Prompt and schema verified byte-identical to the
  previous values.
- Added `parsed_automation_intent()` in `automation_intent.py`: a parse-once boundary reader
  that validates serialized `AutomationIntent.model_dump()` payloads and returns `None` for
  anything that no longer matches the schema. `model_fulfillment._required_surfaces_for_assessment`
  now uses it in place of the `isinstance`/`.get` defensive chain; malformed payloads degrade
  to the same missing-intent discovery default as before (the only consumer coalesces
  `None`/empty identically via `required_surfaces_override or ...` in `discovery/bundle.py`).
  Added `tests/test_automation_intent_payload.py` covering round-trip, non-mapping rejection,
  and schema-drift rejection.

## Verification

- Targeted tests added: `tests/test_capability_registration.py` (10),
  `tests/test_provider_contract.py` (4), `tests/test_capability_routing_rules.py` (3),
  `tests/test_automation_intent_payload.py` (3); no existing test modified.
- Byte-identity evidence: system prompt and schema compared programmatically against
  `git show HEAD` extractions; moved packet functions compared via `inspect.getsource`
  against the pre-split module text; routing reason strings verified against the
  pre-refactor code.
- `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90`
  — ruff clean, mypy --strict clean (165 files), 1298 tests passing (baseline 1278),
  coverage 93.77% (baseline 93.59%).
