# Sprint 496 Change Log

## Automation intent payload non-JSON value rejection

Hardened `_automation_intent_payload()` so capability assessment construction cannot fail through raw Pydantic serializer diagnostics when a corrupted in-process `AutomationIntent` DTO contains unsupported Python values.

Sprint 479 rejected non-finite numeric automation-intent values. This sprint closes the adjacent structural JSON gap: unsupported objects, bytes, and other non-JSON values now fail before `StoryCapabilityAssessment.automation_intent` output, implementation packet assembly, model prompts, or persisted artifacts with the fixed `automation intent payload contains non-JSON values` diagnostic. The diagnostic does not echo intent field names, field labels, story identifiers, object type names, object string output, credential-like keys, or payload values.

The implementation preserves valid Pydantic-native automation-intent values by preflighting Python-mode payloads, then returning the established Pydantic JSON-mode payload shape used by capability assessments.

## Verification

- Added 1 failing-first capability assessment test proving an object with secret-bearing `__str__` output previously surfaced a raw Pydantic serializer diagnostic.
- `python3 -m pytest tests/test_capability_assessment.py::test_automation_intent_payload_rejects_non_json_value_without_leak -q`: failed before implementation because the diagnostic reflected the local object type name.
- `python3 -m pytest tests/test_capability_assessment.py::test_automation_intent_payload_rejects_non_json_value_without_leak tests/test_capability_assessment.py::test_automation_intent_payload_rejects_non_finite_numeric_value_without_leak -q`: 2 tests passed.
- `python3 -m pytest tests/test_capability_assessment.py -q`: 16 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 570 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2435 total tests passed at 93.74% coverage.
