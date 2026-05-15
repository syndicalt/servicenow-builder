# Sprint 129 Change Log

## Flow XML Shape Evidence Validation

Sprint 129 added validation-only Flow XML shape evidence checks for the Flow Designer path.
The Flow XML shape evidence validator is review evidence only.

## Changes

- Added `validate_flow_xml_shape_evidence`.
- Validated retrieved Flow XML review samples against `flow-xml-shapes-v1`.
- Rejected malformed XML, wrong roots, wrong actions, missing required field evidence, and forbidden field evidence.
- Added `xml_shape_evidence_validator_available` to Flow builder preflight evidence.
- Updated ADR 0011, the operator guide, and the production hardening backlog.

## Boundary

There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer. This sprint only proves that reviewed XML evidence samples match the repository contract before future builder work is considered.

## Verification

- Added positive validator coverage for a `sys_hub_action_instance` review sample.
- Added negative validator coverage for missing required field evidence.
- Added negative validator coverage for forbidden field evidence.
- Added documentation coverage for the Sprint 129 boundary.
