# Sprint 7 Change Log

## Scope

Sprint 7 added the minimal review workflow and controlled export preflight required before any ServiceNow XML or sandbox integration work.

## Changes

- Review workflow in `src/jedi_devproject/review.py`.
- Named reviewer approval through `approve_for_export`.
- Rejection workflow through `reject_candidate`.
- `ReviewEvent` with story number, reviewer identity, reason, prior status, next status, and decision timestamp.
- Invalid status transitions blocked through the candidate transition rules from Sprint 1.
- Export preflight through `export_preflight`.
- XML export defaults off through `ReviewSettings`.
- Draft candidates cannot be exported.
- Rejected candidates cannot be approved without a new revision path.

## Assumptions Challenged

- Review state must be enforced before XML export exists.
- CLI-level review primitives are enough for this sprint; a web dashboard remains deferred.
- XML export should stay behind a feature flag until JSON candidate review quality is proven.

## Verification Evidence

Latest full gate run before this change log was added:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result:

- Ruff passed.
- Mypy passed.
- Pytest passed with 57 tests.
- Coverage was 96.52%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
