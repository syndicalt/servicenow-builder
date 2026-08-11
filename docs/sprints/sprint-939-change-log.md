# Sprint 939 Change Log - Model payload exact scalar and container boundaries

## Scope

- Hardened `_ensure_context_dto_payload_json_safe()` for exact JSON scalar and container traversal.
- Hardened `_ensure_capability_payload_json_safe()` for exact JSON scalar and container traversal.
- Documented exact scalar and exact container boundaries for context dossier DTO and automation-intent payload conversion.

## Production Hardening

- Context dossier DTO payloads now accept only exact booleans, integers, finite floats, strings, dictionaries, lists, and tuples at the JSON preflight boundary.
- Capability assessment payloads now accept only exact booleans, integers, finite floats, strings, dictionaries, lists, and tuples at the JSON preflight boundary.
- Dictionary, list, tuple, integer, and float subclasses fail before canonical JSON serialization, context dossier compaction, assessment construction, `items()`, iteration, or subclass hooks can execute.

## Tests

- Added `test_context_dto_payload_rejects_scalar_subclasses_without_payload_leak`.
- Added `test_context_dto_payload_rejects_container_subclasses_without_payload_leak`.
- Added `test_capability_payload_rejects_scalar_subclasses_without_payload_leak`.
- Added `test_capability_payload_rejects_container_subclasses_without_payload_leak`.
- Added `test_sprint_939_documents_model_payload_exact_scalar_container_boundaries`.
- Captured 4 failing-first model payload subclass assertions.
- Focused verification: `5 passed`.
- Scoped verification: `5 passed`; `20 passed`; `1012 passed`.
- Static verification: `ruff check src tests`; `mypy src tests`.
- Full coverage verification: `3594 passed`; total coverage `93.51%`.
