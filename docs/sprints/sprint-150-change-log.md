# Sprint 150 Change Log

## Catalog Item UAT hardening

- Fixed a UAT defect where a model-generated Catalog Item candidate could pass a blank catalog variable label into handoff and fail before retrieved Update Set creation.
- Added candidate reconciliation for `catalog_item_create`: the model response must still pass table, operation, test-plan, and rollback validation, but the catalog mutation payload is rebuilt from the normalized story intent before artifact persistence and handoff.
- Preserved the ServiceNow review boundary: the output remains a retrieved Update Set containing `sc_cat_item`, `item_option_new`, `sc_cat_item_category`, and `m2m_connected_content` customer updates.
- Added a regression test for the STRY0010025 failure mode to ensure variables are emitted with canonical `question_text`, reference table, and reference qualifier values from the structured story.

## Verification

- `pytest tests/test_implementation_packet.py::test_catalog_candidate_reconciles_variables_from_normalized_intent -q`
- `pytest tests/test_implementation_packet.py tests/test_catalog_item_generation.py tests/test_update_set_handoff.py tests/test_model_fulfillment.py -q`
- `ruff check .`
- `mypy src tests`
- `pytest --cov=src/jedi_devproject --cov-report=term-missing`
- Result: `794 passed`, total coverage `90.23%`.
- UAT rerun: `STRY0010025` moved to `Ready for testing`, created retrieved Update Set `JEDI STRY0010025 - AI Candidate`, and produced six customer updates for the catalog item, three variables, catalog category relation, and Employee Center connected-content relation.
