# Sprint 1009 Change Log - Flow XML evidence record collection guard

## Summary

Hardened Flow XML evidence collection so live ServiceNow Flow evidence lookups validate record containers before Flow matching, shape validation, snapshot hashing, or readiness evaluation.

## Security

`collect_flow_xml_evidence()`, `_flow_instance_sys_ids()`, `_collect_shape_evidence()`, and `_collect_snapshot_evidence()` now route `sys_hub_flow`, `sys_hub_action_instance`, `sys_hub_flow_logic_instance_v2`, `sys_update_xml`, and `sys_hub_flow_snapshot` fetch results through `_flow_evidence_records()`.

The helper accepts only exact Python lists containing exact Python dictionaries and fails closed with `Flow XML evidence records contain non-JSON value`.

Malformed Flow XML evidence containers fail before list truthiness, length checks, indexing, record `.get()` hooks, flow sys_id parsing, instance sys_id extraction, customer-update lookup, XML shape validation, snapshot JSON hashing, metadata rendering, readiness evaluation, artifact persistence, or work-note generation can consume caller-controlled container behavior.

## Tests

- Added 1 failing-first Flow XML evidence record collection subclass assertion: `test_collect_flow_xml_evidence_rejects_flow_record_collection_subclass_without_leak`.
- Added 1 failing-first Flow XML evidence record subclass assertion: `test_collect_flow_xml_evidence_rejects_flow_record_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1009_documents_flow_xml_evidence_record_collection_guard`.

## Verification

- `pytest tests/test_flow_xml_evidence.py::test_collect_flow_xml_evidence_rejects_flow_record_collection_subclass_without_leak tests/test_flow_xml_evidence.py::test_collect_flow_xml_evidence_rejects_flow_record_subclass_without_leak -q` failed before implementation because unsafe collection truthiness and record `.get()` hooks executed.
- `pytest tests/test_flow_xml_evidence.py::test_collect_flow_xml_evidence_rejects_flow_record_collection_subclass_without_leak tests/test_flow_xml_evidence.py::test_collect_flow_xml_evidence_rejects_flow_record_subclass_without_leak tests/test_flow_xml_evidence.py::test_collects_and_validates_all_flow_xml_shape_evidence -q` - 3 passed.
