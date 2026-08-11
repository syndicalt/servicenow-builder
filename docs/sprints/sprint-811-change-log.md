# Sprint 811 Change Log - Public production HSTS max-age floor

## Scope

Hardened public production Strict Transport Security validation so API-facing production roles cannot
start with an enabled but trivially short HSTS lifetime.

## Tests First

- Added 2 failing-first public production HSTS max-age assertions:
  `tests/test_runtime.py::test_validate_runtime_settings_rejects_short_hsts_max_age_on_public_production_roles`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_811_documents_public_production_hsts_max_age_floor`.
- Initial failures proved `JEDI_RUNTIME_ROLE=api` and explicitly accepted
  `JEDI_RUNTIME_ROLE=combined` production runtimes accepted
  `JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS=300`.

## Changes

- `JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS` now has a public production minimum.
- Added a one-year public production HSTS floor:
  `JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS>=31536000`.
- The existing default remains `31536000`.
- Development and worker-only runtimes remain free to omit HSTS for local HTTP and private worker
  topologies.
- Updated the operator guide to document the production max-age floor.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "short_hsts_max_age_on_public_production_roles or requires_hsts_on_public_production_roles or api_role_does_not_require_model_provider"`: 5 passed, 357 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_811`: 1 passed, 883 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 362 passed.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_811 or two_hundred_twenty_two_documents_strict_transport_security"`: 2 passed, 882 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3220 passed, 93.38% coverage.
