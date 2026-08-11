# Sprint 649 Change Log

## Implementation-packet response table exact-string boundary

Sprint 649 continued production hardening by tightening model/provider table names used during implementation-packet capability matching. The table/capability validator already sanitized unexpected table-name diagnostics, but it extracted table names with `str(change.get("table") or "").strip()`. A malformed in-process provider response could use a non-string table object that executed custom string conversion before capability matching completed.

Model-proposed table names now must be exact strings before trimming, expected-table comparison, or diagnostic rendering. Non-string table values and string subclasses fail closed with `model response table names must be exact strings`. Existing unexpected-table diagnostics still redact, normalize, and cap valid string table names before they are included in `ModelResponseError`.

Verification:

- Added 1 failing-first packet-validation test proving a hostile provider-response table object executed `__str__` before implementation.
- `python3 -m pytest tests/test_packet_validation.py::test_table_capability_mismatch_rejects_table_object_without_leak -q`: failed before implementation because the hostile `__str__` hook ran.
- `python3 -m pytest tests/test_packet_validation.py::test_table_capability_mismatch_rejects_table_object_without_leak tests/test_packet_validation.py::test_table_capability_mismatch_sanitizes_model_table_names tests/test_packet_validation.py::test_implementation_contract_rejects_non_string_review_items_without_echo tests/test_packet_validation.py::test_raw_xml_validation_rejects_non_string_dict_key_without_leak -q`: 4 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_649_documents_response_table_exact_string_boundary -q`: 1 test passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: no issues found in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 723 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2,788 tests passed with 93.00% coverage.
