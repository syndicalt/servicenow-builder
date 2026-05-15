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
