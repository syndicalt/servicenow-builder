# Sprint 95 Change Log

## Goal

Prepare the next UAT story for a Problem-table vendor reference field without generating incomplete reference dictionary metadata.

## Changes

- Created draft UAT story `STRY0010002` in the PDI for adding `problem.u_vendor_reference` below Description.
- Extended dictionary/form intent metadata with `reference_table` and `reference_qualifier`.
- Parsed reference field stories that specify `core_company` and `vendor=true`.
- Generated ServiceNow dictionary XML for reference fields with:
  - `reference=core_company`
  - `use_reference_qualifier=simple`
  - `reference_qual=vendor=true`
  - `reference_qual_condition=vendor=true`
- Added validation so reference fields cannot generate XML without a reference table.
- Normalized model-produced table names such as `Problem`, `Problem table`, and `Problem form` to `problem` before form metadata lookup.

## Tests

- Added capability analysis coverage for the `STRY0010002` Problem vendor reference story.
- Added generic dictionary/form XML coverage for reference metadata.
- Added retrieved Update Set handoff coverage proving reference metadata is preserved.
- Added a fail-closed validation test for incomplete reference field intents.
- Added a regression for mixed-case model table names after the first `STRY0010002` UAT retry failed with `dictionary/form handoff changes must target the same table`.
- Verified `STRY0010002` live after deployment on May 14, 2026:
  - Story sys_id `c07ba0a2c3b4c710913fbf12b4013110` moved to `state=-7` and `u_ai_status=Ready for Testing`.
  - Retrieved Update Set `JEDI STRY0010002 - AI Candidate` was created as `f9680f4f5007a87d5cb0b6d63edca76e` in `loaded` state.
  - The retrieved Update Set contained three customer updates: `sys_dictionary_problem_u_vendor_reference`, `sys_documentation_problem_u_vendor_reference_en`, and `sys_ui_section_bfb81dc9c0a8000900127627db594210`.
  - The dictionary customer update included `reference=core_company`, `use_reference_qualifier=simple`, `reference_qual=vendor=true`, and `reference_qual_condition=vendor=true`.

## Decision

Do not trigger `STRY0010002` until reference-field support is deployed. A reference field is still low-risk, but it is not equivalent to a plain string field because the dictionary record must include reference target and qualifier metadata.
