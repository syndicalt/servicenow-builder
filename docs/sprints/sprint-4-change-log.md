# Sprint 4 Change Log

## Scope

Sprint 4 added template-only candidate generation so the MVP can produce reviewable JSON artifacts without external model calls.

## Changes

- Template-only candidate generation in `src/jedi_devproject/candidates.py`.
- Content-only story generation for the initial narrow allowlist.
- Manual-build routing for unsupported or non-eligible safety results.
- Candidate output with retrieval citations, assumptions, reviewer notes, confidence, risk score, and proposed change records.
- Stable candidate artifact hash stored on `UpdateSetCandidate`.
- Write-once artifact writer in `src/jedi_devproject/artifacts.py`.
- Artifact overwrite protection through `ArtifactWriteError`.
- Candidate artifact JSON written under a run-specific directory.

## Assumptions Challenged

- Template-only generation can prove artifact shape and review flow before model integration.
- JSON candidates remain the correct Sprint 4 output; XML export is still deferred.
- Write-once artifact behavior is required for auditability, even in local development.

## Verification Evidence

Latest full gate run before this change log was added:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result:

- Ruff passed.
- Mypy passed.
- Pytest passed with 39 tests.
- Coverage was 97.58%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
