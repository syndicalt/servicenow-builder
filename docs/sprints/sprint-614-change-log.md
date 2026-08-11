# Sprint 614 Change Log

## Automation-intent payload exact-string boundary

Sprint 614 continued production hardening by requiring exact string values before capability assessment automation-intent payloads are embedded in `StoryCapabilityAssessment`. `_automation_intent_payload()` already rejected non-finite numeric values and unsupported non-JSON values, but string subclasses still passed the DTO payload preflight and could be serialized as ordinary strings.

`_ensure_capability_payload_json_safe()` now accepts exact `str` values and exact `str` mapping keys only. String subclasses fail through the same `automation intent payload contains non-JSON values` diagnostic as other unsupported values, without echoing intent field names, field labels, story identifiers, object output, credential-like keys, or payload values.

Verification:

- Added 1 failing-first capability assessment test proving a string subclass automation-intent payload value was accepted before implementation.
- `python3 -m pytest tests/test_capability_assessment.py::test_automation_intent_payload_rejects_string_subclass_without_leak -q`: failed before implementation because no `ValueError` was raised.
- `python3 -m pytest tests/test_capability_assessment.py -q`: 18 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 688 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2708 tests passed at 93.11% coverage.
