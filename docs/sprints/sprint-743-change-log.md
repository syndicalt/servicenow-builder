# Sprint 743 Change Log - Implementation packet payload cause boundary

## Scope

Hardened implementation packet payload diagnostics so nested DTO and raw normalized-intent conversion
failures do not retain unsafe low-level exception instances as public `ValueError` causes.

## Tests First

- Added 6 failing-first implementation packet payload cause assertions:
  - `tests/test_implementation_packet.py::test_packet_model_payload_rejects_non_finite_assessment_without_payload_leak`
  - `tests/test_implementation_packet.py::test_packet_model_payload_rejects_non_json_assessment_without_payload_leak`
  - `tests/test_implementation_packet.py::test_packet_model_payload_rejects_string_subclass_assessment_without_payload_leak`
  - `tests/test_implementation_packet.py::test_packet_raw_payload_rejects_non_finite_normalized_intent_without_payload_leak`
  - `tests/test_implementation_packet.py::test_packet_raw_payload_rejects_non_json_normalized_intent_without_payload_leak`
  - `tests/test_implementation_packet.py::test_packet_raw_payload_rejects_string_subclass_without_payload_leak`
- Initial failures proved the public `ValueError` retained unsafe causes for:
  - Nested assessment `risk_score` non-finite numeric rejection.
  - Nested assessment `SecretBearingObject` unsupported object rejection.
  - Nested assessment `HostilePacketText` string subclass rejection.
  - Raw normalized intent `estimated_effort` non-finite numeric rejection.
  - Raw normalized intent `SecretBearingObject` unsupported object rejection.
  - Raw normalized intent `HostileRawPacketText` string subclass rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_743_documents_implementation_packet_payload_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original Pydantic serializer causes in `_packet_model_payload()`.
- Suppressed original non-finite numeric validation causes in `_packet_model_payload()`.
- Suppressed original non-JSON structure validation causes in `_packet_model_payload()`.
- Suppressed original non-finite numeric validation causes in `_packet_raw_payload()`.
- Suppressed original non-JSON structure validation causes in `_packet_raw_payload()`.
- Preserved the existing fixed diagnostics:
  - `implementation packet nested payload contains non-finite numeric values`
  - `implementation packet nested payload contains non-JSON values`
  - `implementation packet raw payload contains non-finite numeric values`
  - `implementation packet raw payload contains non-JSON values`
- Documented the implementation packet payload cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_implementation_packet.py -q -k "packet_model_payload_rejects or packet_raw_payload_rejects"`
  failed first with 6 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_743` failed first with 1 failure.
- `python3 -m pytest tests/test_implementation_packet.py -q -k "packet_model_payload_rejects or packet_raw_payload_rejects"`
  passed with 6 tests and 64 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_743` passed with 1 test and 816
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_implementation_packet.py -q` passed with 70 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3073 tests and 93.33% total coverage.
