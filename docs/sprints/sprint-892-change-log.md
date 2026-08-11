# Sprint 892 Change Log

## Catalog item generation string-subclass guard

- Added 1 failing-first catalog item string-subclass assertion: `test_catalog_item_customer_updates_rejects_string_subclass_item_field_without_leak`.
- Catalog item generation text conversion now requires exact strings before item-name normalization, variable metadata parsing, catalog/category/topic/flow lookup, XML generation, ServiceNow import, or story writeback can reuse the value.

## Verification

- Focused red: `pytest tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_string_subclass_item_field_without_leak tests/test_project_docs.py::test_sprint_892_documents_catalog_item_generation_string_subclass_guard -q` failed because catalog item generation accepted string-subclass model fields.
- Focused green: `pytest tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_string_subclass_item_field_without_leak tests/test_project_docs.py::test_sprint_892_documents_catalog_item_generation_string_subclass_guard -q` passed with 2 tests.
- Catalog item suite: `pytest tests/test_catalog_item_generation.py -q` passed with 49 tests.
- Docs suite: `pytest tests/test_project_docs.py -q` passed with 965 tests.
- Full Ruff gate: `python3 -m ruff check src tests` passed.
- Full mypy gate: `python3 -m mypy src tests` passed with 203 source files checked.
- Full coverage gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3494 tests and 93.52% total coverage.
