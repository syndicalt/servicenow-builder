# Sprint 791 Change Log - CI read-only token permissions

## Scope

Hardened GitHub Actions verification permissions so the CI workflow runs with read-only repository
token scope instead of relying on repository or organization defaults.

## Tests First

- Added 4 failing-first CI permission assertions in `tests/test_ci_workflow.py::test_ci_workflow_uses_read_only_token_permissions`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_791_documents_ci_read_only_token_permissions`.
- Initial failures proved `.github/workflows/ci.yml` had no explicit `permissions` block and this sprint log was absent.

## Changes

- Added top-level `permissions: contents: read` to `.github/workflows/ci.yml`.
- Added regression assertions that reject `contents: write` and `pull-requests: write` in the verification workflow.
- Documented that CI checkout needs read scope only and should not receive write-token permissions.

## Verification

- `python3 -m pytest tests/test_ci_workflow.py tests/test_project_docs.py -q -k "read_only_token_permissions or ci_read_only_token"`: 2 passed, 865 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3173 passed, total coverage 93.36%.
