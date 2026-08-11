# Sprint 792 Change Log - CI concurrency cancellation

## Scope

Hardened GitHub Actions verification reliability so stale CI runs are cancelled when a newer commit
arrives for the same workflow and ref.

## Tests First

- Added 4 failing-first CI concurrency assertions in `tests/test_ci_workflow.py::test_ci_workflow_cancels_stale_verification_runs`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_792_documents_ci_concurrency_cancellation`.
- Initial failures proved `.github/workflows/ci.yml` had no concurrency block and this sprint log was absent.

## Changes

- Added top-level CI `concurrency` with `group: ${{ github.workflow }}-${{ github.ref }}` using `github.workflow` and `github.ref`.
- Added `cancel-in-progress: true` so superseded pushes or PR updates cancel stale verification runs.
- Documented the stale-run cancellation behavior in the operator guide.

## Verification

- `python3 -m pytest tests/test_ci_workflow.py tests/test_project_docs.py -q -k "concurrency_cancellation or stale_verification"`: 2 passed, 867 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3175 passed, total coverage 93.36%.
