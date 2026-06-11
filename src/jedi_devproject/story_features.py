"""Story text normalization and feature extraction for capability analysis."""

from __future__ import annotations

import re

from jedi_devproject.capabilities import FieldFormIntent
from jedi_devproject.models import Story
from jedi_devproject.requirement_text import positive_requirement_text


def _story_text(story: Story) -> str:
    return " ".join(
        part
        for part in [story.short_description, story.description, story.acceptance_criteria or ""]
        if part
    ).lower()


def _positive_requirement_text(text: str) -> str:
    return positive_requirement_text(text)


def _form_section_names(text: str) -> list[str]:
    candidates: list[str] = []
    match = re.search(r"(?:hide|remove|not display|will not display) the (.+?) tabs?", text)
    if match:
        candidates.extend(_split_section_labels(match.group(1)))
    for match in re.finditer(r"\b([a-z][a-z0-9 ]+?) tab\b", text):
        candidates.extend(_split_section_labels(match.group(1)))
    return [candidate for candidate in candidates if candidate]


def _split_section_labels(raw_value: str) -> list[str]:
    cleaned = re.sub(r"\b(?:from|on|in) the .*$", "", raw_value).strip(" .:-")
    labels = re.split(r",|\band\b", cleaned)
    return [
        _title_label(label)
        for label in labels
        if label.strip() and label.strip().lower() not in {"the", "tabs", "tab"}
    ]


def _field_form_intent(story: Story, text: str) -> FieldFormIntent | None:
    target_table = _target_table(text)
    field_label = _field_label(text)
    field_name = _field_name(text)
    field_type = _field_type(text)
    if target_table is None or field_type is None or (field_label is None and field_name is None):
        return None
    if field_label is None:
        if field_name is None:
            return None
        normalized_label = field_name.replace("u_", "").replace("_", " ").title()
    else:
        normalized_label = field_label
    return FieldFormIntent(
        target_table=target_table,
        field_label=normalized_label,
        field_name=field_name,
        field_type=field_type,
        reference_table=_reference_table(text),
        reference_qualifier=_reference_qualifier(text),
        max_length=_max_length(text),
        placement_anchor=_placement_anchor(text),
        placement_position=_placement_position(text),
        mandatory="mandatory" in text or "required" in text,
        default_value=str(story.additional_context.get("default_value", "")),
    )


def _target_table(text: str) -> str | None:
    if "script include" in text:
        return "global"
    if _is_cmdb_ire_analysis_request(text):
        return _cmdb_ire_target_table(text)
    if "incident" in text:
        return "incident"
    if "problem" in text:
        return "problem"
    if "dmn_demand" in text or "demand record" in text or "demand form" in text:
        return "dmn_demand"
    if "rm_story" in text or "story form" in text or "story table" in text:
        return "rm_story"
    match = re.search(r"table named ([a-zA-Z0-9_]+)", text)
    if match:
        return match.group(1).lower()
    match = re.search(r"to the ([a-zA-Z0-9_]+) form", text)
    if match:
        return match.group(1).lower()
    return None


def _is_cmdb_ire_analysis_request(text: str) -> bool:
    cmdb_terms = ("cmdb", "configuration item", "ci ", " cis", "device", "devices")
    ire_terms = (
        "ire",
        "identification rule",
        "identification rules",
        "reconciliation rule",
        "reconciliation rules",
        "reconciliation runs",
        "primary unique identifier",
        "primary identifier",
        "match key",
        "matched by",
    )
    source_terms = ("sccm", "intune", "workspace one", "azure arc", "discovery source")
    return (
        any(term in text for term in cmdb_terms)
        and any(term in text for term in ire_terms)
    ) or (
        "serial number" in text
        and "reconciliation" in text
        and any(term in text for term in source_terms)
    )


def _cmdb_ire_target_table(text: str) -> str:
    if any(term in text for term in ["device", "devices", "computer", "sccm", "intune"]):
        return "cmdb_ci_computer"
    if any(term in text for term in ["server", "servers"]):
        return "cmdb_ci_server"
    if "network" in text:
        return "cmdb_ci_netgear"
    return "cmdb_ci"


def _field_label(text: str) -> str | None:
    match = re.search(r"field labeled ([a-zA-Z0-9 _-]+?)(?: exists| is| on| below|\.|\n|$)", text)
    if match:
        return _title_label(match.group(1))
    match = re.search(r"field name: ([a-zA-Z0-9 _-]+)", text)
    if match:
        return _title_label(match.group(1))
    match = re.search(r"field named ([a-zA-Z0-9 _-]+?)(?: and| to| on| below|\.|\n|$)", text)
    if match:
        return _title_label(match.group(1))
    return None


def _field_name(text: str) -> str | None:
    match = re.search(r"\b(u_[a-zA-Z0-9_]+)\b", text)
    return match.group(1).lower() if match else None


def _field_type(text: str) -> str | None:
    match = re.search(r"field type: ([a-zA-Z0-9 _-]+)", text)
    if match:
        return _normalize_field_type(match.group(1))
    for candidate in ["reference", "string", "integer", "boolean", "date", "datetime", "journal"]:
        if candidate in text:
            return _normalize_field_type(candidate)
    if "characters" in text:
        return "string"
    if "custom field" in text:
        return "string"
    return None


def _normalize_field_type(value: str) -> str:
    cleaned = value.strip().lower().replace(" ", "_").replace("-", "_")
    if cleaned in {"date_time", "datetime"}:
        return "glide_date_time"
    if cleaned in {"journal", "journal_input"}:
        return "journal_input"
    return cleaned


def _max_length(text: str) -> int | None:
    match = re.search(r"length: ([0-9]+)", text)
    if match:
        return int(match.group(1))
    return None


def _reference_table(text: str) -> str | None:
    patterns = [
        r"reference the ([a-zA-Z0-9_]+) table",
        r"references ([a-zA-Z0-9_]+)(?: table|\.|\n| |$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).lower()
            if candidate != "field":
                return candidate
    return None


def _reference_qualifier(text: str) -> str | None:
    match = re.search(
        r"(?:reference qualifier of|where|only allow .* where) ([a-zA-Z0-9_]+=[^\\.\\n ]+)", text
    )
    if match:
        return match.group(1)
    return None


def _placement_anchor(text: str) -> str | None:
    if "below description" in text or "below the description" in text:
        return "description"
    match = re.search(r"below ([a-zA-Z0-9_ ]+?)(?: field|\.|\n|$)", text)
    if match:
        return match.group(1).strip().lower().replace(" ", "_")
    return None


def _placement_position(text: str) -> str:
    if "above " in text:
        return "above"
    if "below " in text:
        return "below"
    return "end"


def _title_label(value: str) -> str:
    cleaned = value.strip(" .:-")
    if cleaned.lower().startswith("u_"):
        cleaned = cleaned[2:]
    cleaned = cleaned.replace("_", " ")
    return " ".join(word.capitalize() for word in cleaned.split())
