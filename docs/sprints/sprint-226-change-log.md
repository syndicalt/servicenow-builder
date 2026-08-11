# Sprint 226 Change Log

Scope: Production hardening - HTML admin console Permissions Policy.

## Changes

- Added regression coverage that `/admin` returns a restrictive `Permissions-Policy` disabling camera, microphone, geolocation, payment, USB, motion sensors, and fullscreen.
- Added regression coverage that `/admin/artifacts/{artifact_id}` returns the same browser capability policy.
- Extended JSON admin diagnostic boundary coverage so `/admin/jobs` does not receive the HTML Permissions Policy.
- Added a path-scoped admin HTML `Permissions-Policy` header beside the existing CSP, frame, and referrer policies.
- Documented the disabled browser capabilities and the JSON/HTML boundary.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "disables_browser_capabilities or html_csp"` - 3 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed; 174 source files checked.
- `python3 -m pytest tests/test_project_docs.py -q` - 300 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1557 passed, 93.89% coverage.
