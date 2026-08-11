# Sprint 466 Change Log

## Flow snapshot evidence non-finite number rejection

Hardened Flow Designer snapshot evidence hashing so retrieved `sys_hub_flow_snapshot` rows cannot
produce `content_sha256` values from non-strict JSON containing `NaN`, `Infinity`, or `-Infinity`.
The snapshot hash is used as read-only evidence for Flow builder readiness and UAT review, so a
malformed row should block evidence collection instead of minting a digest over Python-only JSON
tokens.

Snapshot evidence collection now serializes the snapshot row with strict JSON numeric handling
before computing `content_sha256`. If serialization finds a non-finite numeric value, the collector
records `sys_hub_flow_snapshot:invalid`, stores the fixed reason
`flow_snapshot_evidence_invalid: non-finite snapshot value`, leaves `content_sha256` empty, and does
not preserve malformed snapshot metadata. The diagnostic does not echo snapshot field names,
credential-like keys, or values.

## Verification

- Added 1 failing-first Flow snapshot evidence test covering non-finite snapshot rows without
  field-name, credential-key, or value reflection.
- `python3 -m pytest tests/test_flow_xml_evidence.py::test_non_finite_snapshot_record_marks_snapshot_invalid_without_payload_leak -q`:
  failed before implementation because `NaN` snapshot evidence was marked `collected`.
- `python3 -m pytest tests/test_flow_xml_evidence.py::test_collects_and_validates_all_flow_xml_shape_evidence tests/test_flow_xml_evidence.py::test_non_finite_snapshot_record_marks_snapshot_invalid_without_payload_leak tests/test_flow_xml_evidence.py::test_missing_snapshot_reference_marks_snapshot_missing tests/test_flow_xml_evidence.py::test_unretrieved_snapshot_record_marks_snapshot_missing tests/test_flow_xml_evidence.py::test_unstable_snapshot_reference_marks_snapshot_invalid -q`:
  5 tests passed.
- `python3 -m pytest tests/test_flow_xml_evidence.py::test_redacts_script_bodies_and_never_stores_raw_payloads -q`:
  1 test passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 540 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2373 total tests passed at 93.84% coverage.
