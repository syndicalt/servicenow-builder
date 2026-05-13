# Sprint 6 Change Log

## Scope

Sprint 6 added prioritization, repointing suggestions, and run metrics so backlog decisions are explainable and measurable.

## Changes

- Priority scoring in `src/jedi_devproject/planning.py`.
- Scoring formula uses business value, urgency, strategic alignment, recency, effort, and risk.
- Missing optional scoring fields degrade to zero-value inputs and story-points effort fallback.
- Repointing suggestions with evidence.
- Non-mutating story estimates: original story points are never changed by suggestion logic.
- Run metrics for eligible, manual-review, rejected, and generated-candidate counts.

## Assumptions Challenged

- Repointing must produce suggestions, not silent mutation of human estimates.
- Formula weights are product assumptions, not universal truth; they are implemented explicitly so they can be reviewed and changed.
- Missing fields must degrade predictably instead of inventing values.

## Verification Evidence

Latest full gate run before this change log was added:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result:

- Ruff passed.
- Mypy passed.
- Pytest passed with 51 tests.
- Coverage was 96.40%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
