# Sprint 940 Change Log - Artifact container-subclass boundaries

## Scope

- Hardened `_ensure_artifact_hash_payload_json_safe()` so provenance hash payloads traverse only exact dictionaries and lists.
- Hardened `_ensure_artifact_dto_payload_json_safe()` so legacy DTO artifact payloads traverse only exact dictionaries, lists, and tuples.
- Documented artifact hash and DTO artifact container-subclass boundaries in the operator guide.

## Production Hardening

- Artifact hash payload dictionary and list subclasses now fail before `items()`, iteration, canonicalization, or SHA-256 computation.
- Artifact DTO payload dictionary, list, and tuple subclasses now fail before `items()`, iteration, Pydantic DTO artifact serialization, or write-once artifact output.
- Exact dictionaries and lists remain supported for strict JSON provenance hashing; exact dictionaries, lists, and tuples remain supported for Pydantic DTO payload preflight.

## Tests

- Added `test_stable_artifact_hash_rejects_container_subclasses_without_payload_leak`.
- Added `test_artifact_dto_payload_rejects_container_subclasses_without_payload_leak`.
- Added `test_sprint_940_documents_artifact_container_subclass_boundaries`.
- Captured 2 failing-first artifact container-subclass assertions.
- Focused verification: `3 passed`.
- Scoped verification: `20 passed`; `10 passed`; `1013 passed`.
- Static verification: `ruff check src tests`; `mypy src tests`.
- Full coverage verification: `3597 passed`; total coverage `93.48%`.
