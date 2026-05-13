# Sprint 2 Change Log

## Scope

Sprint 2 added rules-first story classification and safety gates so the MVP can reject or route risky work before any model call.

## Changes

- Rules-first story classification in `src/jedi_devproject/safety.py`.
- `AllowlistPolicy` for story type, table, operation, and max-point policy.
- `EligibilityDecision` for `eligible`, `manual_review`, and `rejected`.
- `StoryType` classification for the initial `content_only` allowlist.
- Safety gate engine through `evaluate_story`.
- Operation allowlist enforcement through `proposed_operation`.
- Fail-closed rejection patterns for ACL, role/group, integration, migration, credential handling, and destructive delete language.
- Manual-review routing for stories over max points, missing acceptance criteria, unknown story type, disallowed tables, and disallowed operations.
- Structured machine-readable eligibility reasons.

## Assumptions Challenged

- Story points are not enough to prove safety; table, operation, story type, and rejection-pattern gates are enforced separately.
- A broad classifier would be premature. The initial classifier is intentionally narrow and routes unknown work to manual review.
- The first implementation accidentally defined an operation allowlist without enforcing it; tests caught the gap before Sprint 2 was considered complete.

## Verification Evidence

Latest full gate run before this change log was added:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result:

- Ruff passed.
- Mypy passed.
- Pytest passed with 30 tests.
- Coverage was 97.48%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
