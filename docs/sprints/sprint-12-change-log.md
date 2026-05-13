# Sprint 12 Change Log

## Scope

Sprint 12 added context enrichment before safety evaluation so obvious stories can infer affected table metadata without weakening safety gates.

## Changes

- Context enrichment module in `src/jedi_devproject/enrichment.py`.
- `StoryEnrichmentResult` with original story, enriched story, inferred tables, confidence, and evidence.
- Deterministic affected table inference:
  - portal/help/text/content/copy signals -> `sp_instance`
  - notification/email signals -> `sysevent_email_action`
  - dictionary/field label signals -> `sys_dictionary`
- Pipeline now enriches each story before safety evaluation.
- Pipeline summary now includes `enriched_stories`, `enrichment_manual_review`, and `inferred_tables`.

## Live PDI Result

Manual live run after enrichment:

```bash
PYTHONPATH=src python3 -m jedi_devproject.cli run-pdi --env-file .env --artifact-root artifacts --run-id <timestamped-run-id> --limit 1
```

Observed safe summary:

- `stories_processed=1`
- `eligible=0`
- `manual_review=1`
- `generated_candidates=0`
- `enriched_stories=0`
- `enrichment_manual_review=1`
- `inferred_tables=0`

The result is safe: the PDI story did not contain enough deterministic context to infer an affected table.

## Assumptions Challenged

- Enrichment must not become a broad keyword pile. It is intentionally narrow and evidence-bearing.
- Ambiguous stories remain manual review.
- Candidate generation still requires affected table metadata from either the source story or high-confidence deterministic enrichment.

## Verification Evidence

Latest full gate before this change log was added:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result:

- Ruff passed.
- Mypy passed.
- Pytest passed with 106 tests.
- Coverage was 96.96%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
