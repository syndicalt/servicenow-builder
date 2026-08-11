# Sprint 873 Change Log

## Catalog metadata missing sys_id guard

- Added 1 failing-first catalog metadata missing sys_id assertion: `test_catalog_item_customer_updates_rejects_matched_topic_missing_sys_id`.
- Catalog item customer-update generation now rejects matched catalog metadata records without `sys_id` before relationship XML generation.

## Verification

- Focused import red: `pytest tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_matched_topic_missing_sys_id tests/test_project_docs.py::test_sprint_873_documents_catalog_metadata_missing_sys_id_guard -q` first failed because the new diagnostic constant did not exist.
- Focused behavioral red: `pytest tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_matched_topic_missing_sys_id tests/test_project_docs.py::test_sprint_873_documents_catalog_metadata_missing_sys_id_guard -q` then failed because the matched topic record without `sys_id` did not raise `ValueError`.
- Focused green: `pytest tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_matched_topic_missing_sys_id tests/test_project_docs.py::test_sprint_873_documents_catalog_metadata_missing_sys_id_guard -q` passed with 2 tests.
- Catalog suite: `pytest tests/test_catalog_item_generation.py -q` passed with 48 tests.
- Docs suite: `pytest tests/test_project_docs.py -q` passed with 946 tests.
- Full gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3449 tests and 93.54% total coverage.
