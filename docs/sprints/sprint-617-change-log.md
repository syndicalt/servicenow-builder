# Sprint 617 Change Log

## Context dossier DTO exact-string boundary

Sprint 617 continued production hardening by requiring exact string values before model-facing context dossier DTO payloads are compacted or returned. `_context_model_payload()` already rejected non-finite numeric values and unsupported non-JSON values, but string subclasses still passed the context DTO payload preflight and could be serialized as ordinary strings.

`_ensure_context_dto_payload_json_safe()` now accepts exact `str` values and exact `str` mapping keys only. String subclasses fail through the same `context dossier DTO payload contains non-JSON values` diagnostic as other unsupported values, without echoing context field names, ServiceNow evidence values, story identifiers, object output, credential-like keys, or payload values.

Verification:

- Added 1 failing-first packet context test proving a string subclass context DTO payload value was accepted before implementation.
- `python3 -m pytest tests/test_packet_context.py::test_context_model_payload_rejects_string_subclass_dto_without_payload_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_packet_context.py -q`: 3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 691 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2714 tests passed at 93.11% coverage.
