# Example Story Change Log

## Scope

Added a synthetic content-only story that demonstrates the happy path for template candidate generation.

## Changes

- Synthetic content-only story fixture at `examples/stories/content-only-help-text.json`.
- Example includes description, acceptance criteria, points, priority, data classification, affected table metadata, and safe additional context.
- Example README with a local `run-local` command.
- CLI sample loading now accepts either a single story object or a list of story objects.
- Local example run generated candidate artifact `artifacts/example-content-story/STORY-EXAMPLE-001.json`.

## Assumptions Challenged

- Safety rejection keywords are conservative and do not understand negated constraints. The example avoids prohibited terms instead of weakening the gate.
- A valid happy-path story must include affected table metadata; without it, the correct result is manual review.

## Verification Evidence

Example command:

```bash
PYTHONPATH=src python3 -m jedi_devproject.cli run-local --sample-file examples/stories/content-only-help-text.json --artifact-root artifacts --run-id example-content-story
```

Observed result:

- `stories_processed=1`
- `eligible=1`
- `generated_candidates=1`
- `artifact_count=1`
