# Sprint 804 Change Log - Env example role and HSTS controls

## Scope

Aligned `.env.example` with the production hardening controls that operators now need to configure
intentionally.

## Tests First

- Added 4 failing-first env example runtime control assertions in
  `tests/test_container_runtime.py::test_env_example_documents_runtime_role_and_hsts_controls`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_804_documents_env_example_role_and_hsts_controls`.
- Initial failures proved `.env.example` did not expose the runtime role selector or HSTS controls.

## Changes

- Added `JEDI_RUNTIME_ROLE=combined` to `.env.example` so local development defaults are explicit.
- Added `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=false` to `.env.example`.
- Added `JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS=31536000` to `.env.example`.
- Added an inline note that public production API roles must enable HSTS only after HTTPS is final.

## Verification

- `python3 -m pytest tests/test_container_runtime.py -q -k runtime_role_and_hsts_controls`: 1 passed, 33 deselected.
- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "runtime_role_and_hsts_controls or sprint_804"`: 2 passed, 909 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3201 passed, 93.36% coverage.
