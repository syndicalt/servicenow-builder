# Sprint 772 Change Log - Container audit-root default

## Scope

Hardened the API and worker container images so local audit output has an explicit, owned default
path inside the application runtime directory.

## Tests First

- Added 3 failing-first audit-root container assertions in
  `tests/test_container_runtime.py::test_runtime_dockerfiles_define_owned_audit_root_default`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_772_documents_container_audit_root_default`.
- Initial failures proved `Dockerfile`, `Dockerfile.worker`, the operator guide, and this sprint
  log did not define or document an image-level `JEDI_AUDIT_ROOT=/app/artifacts/audit` contract.

## Changes

- Added `ENV JEDI_AUDIT_ROOT=/app/artifacts/audit` to the API image.
- Added `ENV JEDI_AUDIT_ROOT=/app/artifacts/audit` to the worker image.
- Created `/app/artifacts/audit` in both images before switching to `USER jedi`.
- Documented the container audit-root default in the operator guide.

## Verification

- Focused regression: `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "audit_root_default or sprint_772"` -> 2 passed, 853 deselected.
- Static lint: `python3 -m ruff check src tests` -> passed.
- Static typing: `python3 -m mypy src tests` -> passed.
- Full coverage gate: `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` -> 3136 passed, 93.36% coverage.
