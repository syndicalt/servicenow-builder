# Sprint 762 Change Log - Model intent validator cause boundary

## Scope

Hardened catalog and record-producer model intent validator diagnostics so rejected normalized intent fragments do not retain unsafe lower-level validator or Pydantic exceptions as public causes.

## Tests First

- Added 6 failing-first model intent validator cause assertions:
  - `tests/test_implementation_packet.py::test_catalog_changes_reject_non_declarative_reference_qualifier`
  - `tests/test_implementation_packet.py::test_record_producer_changes_reject_non_declarative_reference_qualifier`
  - `tests/test_implementation_packet.py::test_catalog_changes_reject_rule_with_non_declarative_condition`
  - `tests/test_implementation_packet.py::test_catalog_changes_reject_script_with_invalid_action_or_type`
  - `tests/test_catalog_item_generation.py::test_catalog_variable_intent_reference_qualifier_error_does_not_retain_cause`
- Initial failures proved `reference qualifier rejected`, `condition rejected`, and `action rejected` diagnostics retained lower-level validator or Pydantic exceptions on `__cause__`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_762_documents_model_intent_validator_cause_boundary`
- The documentation assertion was added before the sprint log and operator guide update, so the docs gate covers the new operator-facing contract.

## Changes

- Suppressed original catalog variable reference qualifier validator causes.
- Suppressed original record producer variable reference qualifier validator causes.
- Suppressed original catalog UI policy condition validator causes.
- Suppressed original catalog client script action and rendering validator causes.
- Preserved fixed diagnostics:
  - `reference qualifier rejected`
  - `condition rejected`
  - `action rejected`
- Documented the model intent validator cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_implementation_packet.py tests/test_catalog_item_generation.py -q -k "non_declarative_reference_qualifier or non_declarative_condition or invalid_action_or_type or reference_qualifier_error_does_not_retain_cause"` - 5 passed, 112 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_762` - 1 passed, 835 deselected.
- `python3 -m pytest tests/test_implementation_packet.py tests/test_catalog_item_generation.py -q` - 117 passed.
- `ruff check src tests` - passed.
- `mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3106 passed, 93.39% coverage.
