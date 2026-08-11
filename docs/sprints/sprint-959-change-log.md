# Sprint 959 Change Log - Retrieved Update Set handoff remote_sys_id source guard

## Scope

- Hardened `_remote_sys_id()` so retrieved Update Set id generation does not use generic truthiness on candidate artifact hashes.
- Added `_remote_sys_id_source()` to choose only exact string source values before lowercase conversion and hex filtering.
- Documented the retrieved Update Set `remote_sys_id` source boundary in the operator guide.

## Production Hardening

- Malformed, non-string, or string-subclass candidate artifact hashes are skipped before `remote_sys_id` generation.
- A non-empty exact artifact hash remains the preferred idempotency source; otherwise the exact candidate name is used; otherwise a fixed fallback seed is used.
- Retrieved Update Set id generation no longer allows corrupted candidate hash/name values to execute `__bool__`, `lower()`, `str()`, `repr()`, or custom string methods before XML serialization or post-import lookup construction.

## Tests

- Added `test_create_update_set_handoff_remote_sys_id_ignores_malformed_hash`.
- Captured 1 failing-first retrieved Update Set handoff remote_sys_id source assertion.
- Focused verification passed: 3 tests.
- Scoped verification passed: `tests/test_update_set_handoff.py` 37 tests and `tests/test_project_docs.py` 1032 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3643 tests at 93.25% coverage.
