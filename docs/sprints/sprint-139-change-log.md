# Sprint 139 Change Log

## Supported ServiceNow artifact testing

- Started the live UAT matrix for supported ServiceNow artifact testing across dictionary/form, Business Rule, Client Script, Script Include, and UI Policy stories.
- The first live run exposed two production defects before the matrix could complete:
  - dictionary/form model calls could exceed the OpenAI project token limit because the model payload included every discovered surface plus duplicate instance context.
  - Script Include stories could be blocked by table/form context requirements even though Script Include generation only requires `script_includes` context.

## Model payload compaction

- Added model payload compaction for `instance_context_bundle`.
- Model calls now include only required surfaces and bounded record lists.
- When a surface bundle is present, the payload omits the duplicate top-level `instance_context`.
- Full uncompact context remains stored in the implementation packet artifact for audit.

## Script Include context sufficiency

- Script Include-only context no longer requires table schema or form layout context.
- `table_schema` and `form_layout` surfaces are marked required only when requested by the capability profile.

## Live UAT matrix status

- Initial live UAT batch: `STRY0010003` through `STRY0010007`.
- The batch is not accepted as a pass because the first run surfaced defects.
- The supported artifact live UAT matrix must be rerun after deployment of this sprint.
