# Sprint 149 Change Log

## Catalog Item and Employee Center topic baseline

- Added the `catalog_item_create` capability for standard Catalog Item generation.
- Added structured intent parsing for catalog item name, short description, catalog, category, taxonomy, Employee Center topic, and compact variable definitions.
- Added catalog surface discovery for active catalogs, categories, Employee Center topics, taxonomies, and Catalog Item connected-content metadata.
- Added a retrieved Update Set customer-update builder for:
  - `sc_cat_item`
  - `item_option_new`
  - `sc_cat_item_category`
  - `m2m_connected_content`
- Kept the first catalog scope narrow: no Record Producers, fulfillment flows, approvals, variable sets, catalog scripts, catalog UI policies, user criteria, pricing, images, attachments, order guides, bundles, or topic/taxonomy creation.
- Prevented generic UI Policy and Client Script stories that mention `category` from pulling catalog context unless the story actually requests catalog or Employee Center work.

## Verification

- `ruff check .`
- `mypy src tests`
- `pytest --cov=src/jedi_devproject --cov-report=term-missing`
- Result: `793 passed`, total coverage `90.34%`.
