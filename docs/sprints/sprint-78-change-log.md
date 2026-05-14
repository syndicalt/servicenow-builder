# Sprint 78 Change Log

## Goal

Wire ChatGPT/OpenAI into the fulfillment pipeline as a gated implementation-candidate generator without allowing model output to mutate ServiceNow.

## Changes

- Added `model_candidate_fulfillment_handler` to build a validated implementation packet, call the configured model provider, validate the response, and write reviewed candidate artifacts.
- Added runtime OpenAI configuration fields for `JEDI_MODEL_PROVIDER=openai`, `OPENAI_API_KEY`, and `OPENAI_MODEL`.
- Kept provider activation explicit: `OPENAI_API_KEY` alone does not enable model calls.
- Composed runtime fulfillment so the guarded build-claim path runs first, then the model candidate stage runs only when OpenAI mode is explicitly configured.
- Recorded generated `implementation_packet` and `implementation_candidate` artifacts through `artifact_refs` before completing the fulfillment job.
- Wrote a ServiceNow work note summarizing generated packet and candidate artifact paths.

## Verification

- Added model fulfillment tests proving valid model output writes packet and candidate artifacts.
- Added negative model fulfillment coverage proving unsafe model responses fail closed before artifact or work-note writeback.
- Added runtime tests for explicit OpenAI activation and disabled-by-default behavior.
- Added worker tests proving artifact refs are recorded before job completion.

## Architecture Notes

Sprint 78 does not give ChatGPT authority to apply ServiceNow changes. The model receives a deterministic implementation packet and may produce an implementation candidate only. Deterministic allowlists, model response validation, artifact audit, and downstream review remain the enforcement points. There is intentionally no ServiceNow mutation from model-generated changes in this sprint.
