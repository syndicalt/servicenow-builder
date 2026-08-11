# Sprint 619 Change Log

## Implementation packet raw payload strict JSON boundary

Sprint 619 continued production hardening by adding a recursive strict-JSON preflight to `_packet_raw_payload()` before already-normalized intent dictionaries are attached to implementation packets. The raw payload path already rejected non-finite numeric values through `json.dumps(..., allow_nan=False)`, but unsupported Python objects still raised raw serializer `TypeError` diagnostics and string subclasses could be serialized as ordinary strings.

`_ensure_packet_raw_payload_json_safe()` now accepts JSON primitives, arrays, exact `str` values, and exact `str` mapping keys only. Unsupported objects and string subclasses fail through the fixed `implementation packet raw payload contains non-JSON values` diagnostic, without echoing normalized-intent field names, operator feedback, story identifiers, object output, credential-like keys, or payload values.

Verification:

- Added 2 failing-first implementation packet tests proving unsupported raw payload objects leaked raw `TypeError` diagnostics and string subclass raw payload values were accepted before implementation.
- `python3 -m pytest tests/test_implementation_packet.py::test_packet_raw_payload_rejects_non_json_normalized_intent_without_payload_leak -q`: failed before implementation with raw `TypeError`.
- `python3 -m pytest tests/test_implementation_packet.py::test_packet_raw_payload_rejects_string_subclass_normalized_intent_without_payload_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_implementation_packet.py -q`: 69 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 693 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2719 tests passed at 93.10% coverage.
