# Sprint 167 Change Log

## Scope

Production edge abuse-control hardening. This sprint adds an application-level admin
diagnostic request body bound so public admin/artifact diagnostic routes do not rely only on
GET semantics or external edge infrastructure to reject oversized payloads.

## Changes

- Added `JEDI_ADMIN_MAX_BODY_BYTES` to runtime settings with an 8 KiB default.
- Added production validation that `JEDI_ADMIN_MAX_BODY_BYTES` must be greater than 0.
- Added admin diagnostic route body-size enforcement for `/admin`, `/artifacts/*`, and
  `/jobs/*` routes.
- Oversized admin diagnostic requests now return `413 admin request payload is too large`
  before artifact, job, list, or console handlers query the operational store.
- Updated `docs/operator-guide.md` to document the admin request body bound and the
  remaining need for approved edge, WAF, or API gateway controls in production.

## Verification

- Focused red/green tests:
  `python3 -m pytest tests/test_runtime.py -k "admin_json_endpoint_rejects_oversized_request_body_before_store_access or admin_artifact_endpoint_rejects_oversized_request_body_before_store_access" -q`
  — 2 passed after implementation.
- Runtime regression:
  `python3 -m pytest tests/test_runtime.py -q`
  — 66 passed.
- Full quality gate:
  `python3 -m ruff check src tests`
  — passed.
- Full type gate:
  `python3 -m mypy src tests`
  — passed.
- Full coverage gate:
  `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  — 1315 passed, 93.79% coverage.

## Notes

- This is defense in depth. It does not replace Federal production edge controls for request
  size, rate, IP reputation, WAF policy, DDoS protection, or alerting.
- Admin routes remain read-only. This sprint does not add operator mutation actions.
