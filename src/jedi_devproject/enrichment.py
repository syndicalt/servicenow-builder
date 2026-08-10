from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from jedi_devproject.models import Story


class StoryEnrichmentResult(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    original_story: Story
    enriched_story: Story
    inferred_tables: list[str]
    confidence: float
    evidence: list[str]


def enrich_story(story: Story) -> StoryEnrichmentResult:
    if story.affected_tables:
        return StoryEnrichmentResult(
            original_story=story,
            enriched_story=story,
            inferred_tables=[],
            confidence=1.0,
            evidence=["affected tables already provided"],
        )

    text = f"{story.short_description} {story.description}".lower()
    inferences = _infer_tables(text)
    if not inferences:
        return StoryEnrichmentResult(
            original_story=story,
            enriched_story=story,
            inferred_tables=[],
            confidence=0.0,
            evidence=["no deterministic table inference"],
        )

    inferred_tables = [table for table, _evidence in inferences]
    evidence = [item_evidence for _table, item_evidence in inferences]
    enriched_story = story.model_copy(update={"affected_tables": inferred_tables})
    return StoryEnrichmentResult(
        original_story=story,
        enriched_story=enriched_story,
        inferred_tables=inferred_tables,
        confidence=0.85,
        evidence=evidence,
    )


def _infer_tables(text: str) -> list[tuple[str, str]]:
    if _is_dictionary_form_story(text):
        return [
            ("sys_dictionary", "dictionary field signal"),
            ("sys_ui_form", "form placement signal"),
        ]

    if "portal" in text and _contains_any(text, {"help", "text", "content", "copy"}):
        return [("sp_instance", "portal content signal")]

    if _contains_any(text, {"notification", "email"}):
        return [("sysevent_email_action", "notification content signal")]

    if "dictionary" in text or ("field" in text and "label" in text):
        return [("sys_dictionary", "dictionary field signal")]

    return []


def _contains_any(text: str, needles: set[str]) -> bool:
    return any(needle in text for needle in needles)


def _is_dictionary_form_story(text: str) -> bool:
    has_field_signal = "field" in text or "column" in text or "u_" in text
    has_form_signal = "form" in text or "place" in text
    has_table_signal = "table" in text or "rm_story" in text
    return has_field_signal and has_form_signal and has_table_signal
