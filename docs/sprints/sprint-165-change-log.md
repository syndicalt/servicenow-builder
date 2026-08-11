# Sprint 165 Change Log

## Scope

Production runtime configuration and diagnostic redaction hardening. This sprint tightens
fail-closed startup validation for API and worker entrypoints and improves safe admin
diagnostics without adding any ServiceNow mutation surface.

## Changes

- Added production validation for weak lifecycle HMAC secrets. `JEDI_LIFECYCLE_WEBHOOK_SECRET`
  must be at least 32 characters when `JEDI_ENVIRONMENT=production`.
- Added production validation for non-positive runtime bounds: lifecycle skew, lifecycle body
  bytes, lifecycle/admin rate-limit counts and windows, public-web response bytes,
  public-web excerpt chars, public-web result count, and public-web timeout.
- Added production validation that `JEDI_PUBLIC_WEB_DOC_URLS` entries are HTTPS URLs whose
  hosts exactly match `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS` when public documentation retrieval is
  enabled.
- Added production validation that the legacy `JEDI_UPDATE_SET_APPLY=true` path requires
  `JEDI_UPDATE_SET_USER_NAME`, preserving an operator identity if that backward-compatible
  utility is explicitly enabled.
- Hardened admin diagnostic redaction so JSON and HTML admin views redact URL credentials
  and sensitive query values such as `access_token`, `client_secret`, and `signature`.
- Updated `docs/operator-guide.md` to describe the stronger production fail-closed runtime
  checks and diagnostic redaction boundary.

## Verification

- Focused red/green tests:
  `python3 -m pytest tests/test_runtime.py -k "validate_runtime_settings_rejects_production_weak_webhook_secret or validate_runtime_settings_rejects_non_positive_runtime_limits or validate_runtime_settings_rejects_public_web_docs_outside_allowlist or validate_runtime_settings_rejects_update_set_apply_without_operator" -q`
  — 4 passed after implementation.
- Runtime regression:
  `python3 -m pytest tests/test_runtime.py -q`
  — 61 passed.
- Full quality gate:
  `python3 -m ruff check src tests`
  — passed.
- Full type gate:
  `python3 -m mypy src tests`
  — passed.
- Full coverage gate:
  `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  — 1308 passed, 93.81% coverage.

## Notes

- This sprint intentionally does not enable production `oidc` or `servicenow_oauth` admin
  authentication. Those modes remain fail-closed until designed and tested.
- This sprint does not alter the reviewed retrieved Update Set handoff boundary.
