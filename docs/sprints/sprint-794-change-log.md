# Sprint 794 Change Log - CI third-party action SHA pinning

## Scope

Hardened GitHub Actions supply-chain posture by pinning third-party workflow actions to immutable
commit SHAs instead of mutable major-version tags.

## Tests First

- Added 3 failing-first CI action pinning assertions in `tests/test_ci_workflow.py::test_ci_workflow_pins_third_party_actions_to_commit_shas`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_794_documents_ci_action_sha_pinning`.
- Initial failures proved `.github/workflows/ci.yml` still used mutable `actions/checkout@v4` and `actions/setup-python@v5` refs and this sprint log was absent.

## Changes

- Replaced `actions/checkout@v4` with `actions/checkout@11d5960a326750d5838078e36cf38b85af677262`.
- Replaced `actions/setup-python@v5` with `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`.
- Documented that action SHA updates are intentional dependency-maintenance work, not incidental CI churn.

## Verification

- `python3 -m pytest tests/test_ci_workflow.py tests/test_project_docs.py -q -k "action_sha_pinning or pins_third_party_actions or persist_checkout"`: 3 passed, 870 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3179 passed, 93.36% coverage.
