# Sprint 825 Change Log - Admin Basic-auth encoded policy parity

## Scope

Centralized encoded Basic-auth section validation so pre-decode request-time admin console authentication uses the same shared policy module as decoded credential-part validation.

## Tests First

- Added 1 failing-first Basic-auth encoded section policy assertion: `tests/test_runtime.py::test_admin_basic_auth_encoded_section_policy_is_shared`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_825_documents_admin_basic_auth_encoded_policy_parity`.
- Initial failure proved `jedi_devproject.admin_basic_auth_policy` did not expose encoded-section malformed validation even though it owned `MAX_BASIC_AUTH_ENCODED_BYTES`.

## Changes

- Added `is_malformed_basic_auth_encoded_section()` to `jedi_devproject.admin_basic_auth_policy`.
- Runtime request auth now delegates Basic-auth encoded section padding, control-character, ASCII, and byte-ceiling checks to the shared policy before base64 decoding.
- Updated the operator guide to document that encoded Basic-auth section validation also lives in shared policy.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "admin_basic_auth_encoded_section_policy_is_shared or oversized_basic_auth_payload or padded_basic_auth_payload or non_ascii_basic_auth_payload"` - 5 passed, 374 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_825 or sprint_824"` - 2 passed, 896 deselected.
- `python3 -m pytest tests/test_runtime.py -q` - 379 passed.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 201 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3256 passed, 93.42% coverage.
