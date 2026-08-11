# Sprint 948 Change Log - Client Script list-subclass guard

## Scope

- Hardened `_client_script_string_list()` so Client Script customer-update generation accepts only exact lists before declared field/message metadata iteration.
- Documented the Client Script list-subclass boundary in the operator guide.

## Production Hardening

- List subclasses now fail with `Client Script generation field contains non-JSON value` before iteration.
- Client Script generation no longer allows caller-controlled list iterators to run while deriving fields read, fields written, or messages shown metadata.
- Exact list inputs remain supported for declared `fields_read`, `fields_written`, and `messages_shown` metadata.

## Tests

- Added `test_client_script_customer_updates_rejects_list_subclass_field_without_leak`.
- Captured 1 failing-first Client Script list-subclass iteration assertion.
- Focused verification passed: 2 tests.
- Scoped verification passed: `tests/test_generation_validators.py` 71 tests and `tests/test_project_docs.py` 1021 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3620 tests at 93.26% coverage.
