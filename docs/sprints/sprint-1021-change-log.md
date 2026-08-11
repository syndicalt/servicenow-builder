# Sprint 1021 Change Log - Stable record sys_id part guard

## Summary

Hardened deterministic generated-record sys_id derivation so `stable_record_sys_id()` rejects
string subclasses and non-string objects before joining, encoding, or hashing name parts.

## Security

`stable_record_sys_id()` is used to derive deterministic ServiceNow sys_ids for generated
catalog-family records that need stable references inside retrieved Update Set handoffs. It now
requires every name part to be an exact string; unsupported values fail with
`generation field scalar value contains non-JSON value`.

This prevents malformed in-process generation fields from being accepted as string subclasses and
prevents Python `TypeError` diagnostics from leaking object type names when non-string values reach
record-id derivation.

## Tests

- Added 1 failing-first stable sys_id string-subclass assertion:
  `test_stable_record_sys_id_rejects_string_subclass_without_value_leak`.
- Added 1 failing-first stable sys_id non-string assertion:
  `test_stable_record_sys_id_rejects_non_string_without_type_leak`.
- Added 1 documentation assertion:
  `test_sprint_1021_documents_stable_record_sys_id_part_guard`.

## Verification

- `pytest tests/test_validation_helpers.py::test_stable_record_sys_id_rejects_string_subclass_without_value_leak tests/test_validation_helpers.py::test_stable_record_sys_id_rejects_non_string_without_type_leak -q`
  failed before implementation because string subclasses were accepted and non-string parts raised a
  Python `TypeError` diagnostic with object type details.
