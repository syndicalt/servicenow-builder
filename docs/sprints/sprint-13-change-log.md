# Sprint 13 Change Log

## Scope

Sprint 13 added the first controlled dictionary/form candidate path for `STRY0010013`.

## Changes

- Added `dictionary_form` story type.
- Added deterministic enrichment for add-field-and-place-on-form stories.
- Enrichment now infers both `sys_dictionary` and `sys_ui_form` when field, table, and form-placement signals are present.
- Safety policy can explicitly allow dictionary/form stories without allowing broad dictionary automation.
- Candidate generation now creates a dictionary/form candidate with:
  - `sys_dictionary` insert for `rm_story.u_ai_review_notes`
  - `sys_ui_form` update for Story form placement
- ServiceNow ingestion now fetches and maps `acceptance_criteria`.
- Default runtime policy allows the narrow dictionary/form path.

## Live STRY0010013 Result

Manual live run:

```bash
PYTHONPATH=src python3 -m jedi_devproject.cli run-pdi --env-file .env --artifact-root artifacts --run-id <timestamped-run-id> --limit 1 --sysparm-query "number=STRY0010013"
```

Observed safe summary:

- `stories_processed=1`
- `eligible=1`
- `manual_review=0`
- `generated_candidates=1`
- `artifact_count=1`
- `enriched_stories=1`
- `inferred_tables=2`

Generated artifact:

- `artifacts/stry0010013-dictform-20260513T025701Z/STRY0010013.json`

Artifact structure:

- Status: `Ready for Review`
- Change 1: `sys_dictionary` insert
- Change 2: `sys_ui_form` update
- Confidence: `0.82`
- Risk score: `0.35`

## Assumptions Challenged

- Dictionary changes are riskier than content-only changes, so they require an explicit story type and table allowlist.
- This path is intentionally specific to `rm_story.u_ai_review_notes`; it is not general schema automation.
- Form layout output remains a reviewable candidate, not an import-approved artifact.

## Verification Evidence

Latest full gate before this change log was added:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result:

- Ruff passed.
- Mypy passed.
- Pytest passed with 112 tests.
- Coverage was 97.09%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
