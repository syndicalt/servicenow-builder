# Sprint 764 Change Log - CI verification gate

## Scope

Added a GitHub Actions CI workflow so production hardening gates run on pull requests and pushes to the default `master` branch instead of relying only on local operator discipline.

## Tests First

- Added 2 failing-first CI workflow assertions:
  - `tests/test_ci_workflow.py::test_ci_workflow_enforces_production_verification_gates`
  - `tests/test_ci_workflow.py::test_ci_workflow_uses_safe_shell_defaults`
- Initial failures proved `.github/workflows/ci.yml` did not exist.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_764_documents_ci_verification_gate`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `.github/workflows/ci.yml`.
- The workflow runs on:
  - `pull_request`
  - `push` with `branches: [master]`
- The workflow installs `.[dev]`, then runs:
  - `python3 -m ruff check src tests`
  - `python3 -m mypy src tests`
  - `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
- Workflow command steps use `bash` with `set -euo pipefail`.
- Documented the CI verification gate in the operator guide.

## Verification

- `python3 -m pytest tests/test_ci_workflow.py tests/test_project_docs.py -q -k "ci_workflow or sprint_764"` - 3 passed, 837 deselected.
- `ruff check src tests` - passed.
- `mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3111 passed, 93.39% coverage.
