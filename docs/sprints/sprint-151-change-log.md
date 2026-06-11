# Sprint 151 Change Log

## Catalog variable visibility fix

- Investigated why generated Catalog Item variables existed on `item_option_new` but did not render on the catalog item form.
- Compared generated variables against the manually-created `manual_variable` control record on the same Catalog Item.
- Root cause: generated variables omitted `visible_standalone`, `visible_bundle`, and `visible_summary`, and ServiceNow imported those values as `false`.
- Updated catalog variable customer-update XML to set all three catalog visibility flags to `true`.
- Added regression coverage for both the catalog XML builder and retrieved Update Set handoff XML.

## Verification

- `pytest tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_builds_item_variables_category_and_topic_payloads -q`
- `pytest tests/test_catalog_item_generation.py tests/test_update_set_handoff.py tests/test_implementation_packet.py tests/test_model_fulfillment.py -q`
- `ruff check .`
- `mypy src tests`
- `pytest --cov=src/jedi_devproject --cov-report=term-missing`
- Result: `794 passed`, total coverage `90.23%`.
- UAT rerun: created corrective story `STRY0010026` with sys_id `df38eefac3348b10913fbf12b4013117`; the workflow moved it to `Ready for testing` and created retrieved Update Set `JEDI STRY0010026 - AI Candidate` with sys_id `698c49611f3dc09d0e44dd9a9c2078cc`.
- Verified the retrieved Update Set contains six customer updates and all three generated Catalog Variable payloads include `visible_standalone=true`, `visible_bundle=true`, and `visible_summary=true`.

## Status update (2026-06-11)

- The Sprint 161 builder-maturity routing model moved `catalog_item_create` to candidate generation only. Catalog surfaces score 0.60 builder maturity, below `AUTOMATED_HANDOFF_BUILDER_MATURITY_THRESHOLD = 0.75`, so catalog candidates now route to manual review and the automated retrieved Update Set handoff verified above is no longer created.
- The catalog variable visibility fix remains in the XML builder; automated handoff re-enables when catalog builder maturity crosses the threshold.
- See `_builder_maturity_for_surface()` in `src/jedi_devproject/implementation_packet.py` and the Sprint 161 change log. This note records a later routing change and does not alter the historical record above.
