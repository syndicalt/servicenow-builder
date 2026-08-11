# Sprint 802 Change Log - Public runtime HSTS production gate

## Scope

Hardened production startup validation so public runtime roles cannot start without explicit HTTP
Strict Transport Security enabled.

## Tests First

- Added 2 failing-first public runtime HSTS assertions in
  `tests/test_runtime.py::test_validate_runtime_settings_requires_hsts_on_public_production_roles`.
- Updated the existing API-role production validation fixtures to opt into HSTS where the test is
  proving a different boundary.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_802_documents_public_runtime_hsts_requirement`.
- Initial failures proved `JEDI_RUNTIME_ROLE=api` and `JEDI_RUNTIME_ROLE=combined` could validate in
  production with `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=false`.

## Changes

- `validate_runtime_settings()` now rejects public production runtime roles unless
  `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=true`.
- The check applies to `JEDI_RUNTIME_ROLE=api` and `JEDI_RUNTIME_ROLE=combined`, where lifecycle
  webhooks, health endpoints, readiness checks, and the admin console are HTTP surfaces.
- `JEDI_RUNTIME_ROLE=worker` remains allowed without HSTS because it is not the public API process.
- Documented the production requirement and kept the HTTPS-edge warning explicit: enable HSTS only
  after the public deployment is permanently HTTPS at the approved edge.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "requires_hsts_on_public_production_roles or api_role_does_not_require_model_provider or worker_role_does_not_require_api_secrets"`: 4 passed, 346 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 350 passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_802`: 1 passed, 874 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3196 passed, 93.36% coverage.
