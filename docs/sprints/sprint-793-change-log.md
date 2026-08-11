# Sprint 793 Change Log - CI checkout credential persistence

## Scope

Hardened GitHub Actions checkout behavior so the verification job does not persist the read-only
checkout token into git configuration for later steps.

## Tests First

- Added 3 failing-first CI checkout credential assertions in `tests/test_ci_workflow.py::test_ci_workflow_does_not_persist_checkout_credentials`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_793_documents_ci_checkout_credential_persistence`.
- Initial failures proved `.github/workflows/ci.yml` did not set `persist-credentials: false` on `actions/checkout@v4` and this sprint log was absent.

## Changes

- Added `persist-credentials: false` to the `actions/checkout@v4` step.
- Documented that later lint, typecheck, and test steps should not inherit checkout credentials through git config.

## Verification

- `python3 -m pytest tests/test_ci_workflow.py tests/test_project_docs.py -q -k "checkout_credential_persistence or persist_checkout"`: 2 passed, 869 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3177 passed, 93.36% coverage.
