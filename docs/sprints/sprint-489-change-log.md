# Sprint 489 Change Log

## Flow snapshot evidence non-JSON value rejection

Hardened Flow Designer snapshot evidence hashing so retrieved `sys_hub_flow_snapshot` rows cannot produce `content_sha256` values from Python-only payload values coerced through `str()`.

Sprint 466 rejected non-finite numeric snapshot values. This sprint closes the adjacent provenance gap: unsupported objects, bytes, and other non-JSON row values now mark snapshot evidence invalid before hashing. The collector records `sys_hub_flow_snapshot:invalid`, stores `flow_snapshot_evidence_invalid: non-JSON snapshot value`, leaves `content_sha256` empty, and does not echo malformed field names, object type names, object string output, credential-like keys, or values.

## Verification

- Added 1 failing-first Flow snapshot evidence test proving an object with secret-bearing `__str__` output was previously accepted as collected snapshot evidence.
- `python3 -m pytest tests/test_flow_xml_evidence.py::test_non_json_snapshot_record_marks_snapshot_invalid_without_payload_leak -q`: failed before implementation because the snapshot was marked `collected`.
- `python3 -m pytest tests/test_flow_xml_evidence.py::test_non_json_snapshot_record_marks_snapshot_invalid_without_payload_leak tests/test_flow_xml_evidence.py::test_non_finite_snapshot_record_marks_snapshot_invalid_without_payload_leak tests/test_flow_xml_evidence.py::test_collects_and_validates_all_flow_xml_shape_evidence -q`: 3 tests passed.
- `python3 -m pytest tests/test_flow_xml_evidence.py -q`: 24 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 563 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2421 total tests passed at 93.82% coverage.
