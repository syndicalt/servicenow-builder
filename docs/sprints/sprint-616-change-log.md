# Sprint 616 Change Log

## Implementation packet nested DTO exact-string boundary

Sprint 616 continued production hardening by requiring exact string values before nested implementation packet DTO payloads are returned for provider prompting or artifact persistence. `_packet_model_payload()` already rejected non-finite numeric values and unsupported non-JSON values, but string subclasses still passed the nested DTO payload preflight and could be serialized as ordinary strings.

`_ensure_packet_model_payload_json_safe()` now accepts exact `str` values and exact `str` mapping keys only. String subclasses fail through the same `implementation packet nested payload contains non-JSON values` diagnostic as other unsupported values, without echoing assessment fields, story identifiers, generated values, object output, credential-like keys, or payload values.

Verification:

- Added 1 failing-first implementation packet test proving a string subclass nested DTO payload value was accepted before implementation.
- `python3 -m pytest tests/test_implementation_packet.py::test_packet_model_payload_rejects_string_subclass_assessment_without_payload_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_implementation_packet.py -q`: 67 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 690 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2712 tests passed at 93.11% coverage.
