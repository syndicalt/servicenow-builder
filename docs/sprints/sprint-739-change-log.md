# Sprint 739 Change Log - Capability assessment cause boundary

## Scope

Hardened capability assessment diagnostics so intake feedback hash and automation intent payload
validation failures do not retain unsafe low-level exception instances as public `ValueError` causes.

## Tests First

- Added 6 failing-first capability assessment cause assertions:
  - `tests/test_capability_assessment.py::test_intake_feedback_hash_rejects_non_finite_guidance_without_payload_leak`
  - `tests/test_capability_assessment.py::test_intake_feedback_hash_rejects_non_json_guidance_without_payload_leak`
  - `tests/test_capability_assessment.py::test_build_intake_feedback_rejects_non_finite_guidance_without_payload_leak`
  - `tests/test_capability_assessment.py::test_automation_intent_payload_rejects_non_finite_numeric_value_without_leak`
  - `tests/test_capability_assessment.py::test_automation_intent_payload_rejects_non_json_value_without_leak`
  - `tests/test_capability_assessment.py::test_automation_intent_payload_rejects_string_subclass_without_leak`
- Initial failures proved the public `ValueError` retained unsafe causes for:
  - `guidance` non-finite intake feedback hash payload rejection.
  - `SecretBearingObject` unsupported intake feedback and automation intent payload rejection.
  - `operator_feedback` non-finite build-intake feedback rejection.
  - `max_length` non-finite automation intent payload rejection.
  - `HostileIntentText` string subclass automation intent payload rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_739_documents_capability_assessment_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original non-finite numeric validation causes in `_intake_content_hash()`.
- Suppressed original non-JSON structure validation causes in `_intake_content_hash()`.
- Suppressed original Pydantic serializer causes in `_automation_intent_payload()`.
- Suppressed original non-finite numeric validation causes in `_automation_intent_payload()`.
- Suppressed original non-JSON structure validation causes in `_automation_intent_payload()`.
- Preserved the existing fixed diagnostics:
  - `intake feedback hash payload contains non-finite numeric values`
  - `intake feedback hash payload contains non-JSON values`
  - `automation intent payload contains non-finite numeric values`
  - `automation intent payload contains non-JSON values`
- Documented the capability assessment cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_capability_assessment.py -q -k "hash_rejects or automation_intent_payload_rejects or build_intake_feedback_rejects"`
  failed first with 6 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_739` failed first with 1 failure.
- `python3 -m pytest tests/test_capability_assessment.py -q -k "hash_rejects or automation_intent_payload_rejects or build_intake_feedback_rejects"`
  passed with 6 tests and 12 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_739` passed with 1 test and 812
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_capability_assessment.py -q` passed with 18 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3069 tests and 93.33% total coverage.
