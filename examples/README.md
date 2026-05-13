# Examples

## Content-Only Help Text Story

`examples/stories/content-only-help-text.json` is a synthetic story for the happy-path MVP flow. It includes:

- description
- acceptance criteria
- points
- priority
- affected table metadata
- project-safe context

Run it locally:

```bash
PYTHONPATH=src python3 -m jedi_devproject.cli run-local --sample-file examples/stories/content-only-help-text.json --artifact-root artifacts --run-id example-content-story
```

The fixture is synthetic and contains no customer data or credentials.
