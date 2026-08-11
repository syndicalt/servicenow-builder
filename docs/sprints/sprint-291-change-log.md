# Sprint 291 Change Log - Runtime Enum Auth Mode Diagnostics

## Summary

- Runtime enum env parsing now rejects non-empty values with leading, trailing, or internal whitespace/control characters instead of silently trimming them.
- `JEDI_ADMIN_AUTH_MODE`, `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE`, and `JEDI_PUBLIC_WEB_ACCESS` share the same strict enum whitespace/control boundary.
- Production validation now rejects malformed direct `RuntimeSettings.admin_auth_mode` values before admin-auth posture checks.
- Admin console fallback for unsupported direct auth modes now returns a fixed diagnostic and does not echo arbitrary mode text.
- Existing allowed enum values, reserved fail-closed OIDC/ServiceNow OAuth modes, and development `dev_basic` behavior remain intact.
- Added failing regressions proving enum env whitespace was previously normalized, direct malformed admin auth mode could bypass production validation, and unsupported auth-mode route diagnostics echoed untrusted text.
- Documented the runtime enum and direct admin-auth diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "runtime_enum_boundary_whitespace or malformed_admin_auth_mode_without_echoing_value or unsupported_auth_mode_without_echoing_value"` - 5 tests failed before implementation because enum env whitespace was normalized, malformed direct admin auth mode bypassed production validation, and unsupported auth-mode route diagnostics echoed untrusted text.
- `python3 -m pytest tests/test_runtime.py -q -k "runtime_enum_boundary_whitespace or malformed_admin_auth_mode_without_echoing_value or unsupported_auth_mode_without_echoing_value"` - 5 passed.
- `python3 -m pytest tests/test_runtime.py -q -k "runtime_enum_boundary_whitespace or malformed_admin_auth_mode_without_echoing_value or unsupported_auth_mode_without_echoing_value" && python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_ninety_one_documents_runtime_enum_auth_mode_diagnostics -q` - 5 passed, then 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_auth.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py src/jedi_devproject/runtime_auth.py tests/test_runtime.py tests/test_project_docs.py` - success: no issues found in 4 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 365 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1768 passed; total coverage 93.92%.
