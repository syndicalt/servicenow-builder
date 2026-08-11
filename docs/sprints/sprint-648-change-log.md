# Sprint 648 Change Log

## Implementation-packet raw XML scanner exact-key boundary

Sprint 648 continued production hardening by tightening the raw XML scanner used for implementation-packet provider responses. The scanner was traversal-bounded, but it still normalized object keys with `str(key).strip().lower()` before comparing them against forbidden raw XML field names. A malformed in-process provider response could use a non-string dictionary key that executed custom string conversion while validation was running.

Raw XML scanning now requires provider response object keys to be exact strings before key normalization or recursive descent. Non-string keys and string subclasses fail closed with `model response object keys must be exact strings`. Raw XML content scanning also checks only exact strings, so string subclasses cannot execute custom string methods while XML tokens are evaluated.

Verification:

- Added 1 failing-first packet-validation test proving a hostile provider-response key executed `__str__` before implementation.
- `python3 -m pytest tests/test_packet_validation.py::test_raw_xml_validation_rejects_non_string_dict_key_without_leak -q`: failed before implementation because the hostile `__str__` hook ran.
- `python3 -m pytest tests/test_packet_validation.py::test_raw_xml_validation_rejects_non_string_dict_key_without_leak tests/test_packet_validation.py::test_raw_xml_validation_rejects_raw_xml_content_with_fixed_diagnostic tests/test_packet_validation.py::test_raw_xml_validation_fails_closed_on_excessive_nesting tests/test_packet_validation.py::test_raw_xml_validation_fails_closed_on_excessive_nodes tests/test_packet_validation.py::test_implementation_contract_rejects_too_many_changes tests/test_packet_validation.py::test_implementation_contract_rejects_non_string_review_items_without_echo -q`: 6 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_648_documents_raw_xml_scanner_exact_key_boundary -q`: 1 test passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: no issues found in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 722 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2,786 tests passed with 93.02% coverage.
