# Sprint 143 Change Log

## Business Rule script metadata separation

- Live review of `STRY0010021` found generated Business Rule script code that declared `var fields_written = ["short_description"];`.
- `fields_written` is candidate metadata, not executable ServiceNow script content.
- Business Rule generation now rejects scripts that declare `fields_written` inside the script body instead of silently stripping or rewriting the code.
- The OpenAI provider prompt now explicitly says `fields_written` belongs in JSON field metadata only and must not be emitted as a script variable.
- Business Rule generation also accepts `filter` as a condition alias when the model emits it instead of `filter_condition`.
- This keeps the retrieved Update Set review boundary intact while preventing metadata scaffolding from leaking into `sys_script.script`.
