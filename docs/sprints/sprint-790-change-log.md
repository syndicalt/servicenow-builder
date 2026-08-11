# Sprint 790 Change Log - Compose loopback API binding

## Scope

Hardened local compose network exposure so the API service binds to host loopback instead of every
host interface by default.

## Tests First

- Added 4 failing-first compose port binding assertions in `tests/test_container_runtime.py::test_compose_binds_api_port_to_loopback_only`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_790_documents_compose_loopback_api_binding`.
- Initial failures proved `docker-compose.yml` still published broad `8000:8000` and this sprint log was absent.

## Changes

- Replaced the API compose port binding with `127.0.0.1:8000:8000`.
- Documented that local webhook and admin-console testing remains available on loopback.
- Documented that broader exposure requires an explicit operator edit instead of being the default.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "loopback_api_binding or binds_api_port"`: 2 passed, 887 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3171 passed, total coverage 93.36%.
