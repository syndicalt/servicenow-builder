from __future__ import annotations

import pytest

from jedi_devproject.form_section_generation import (
    _normalize_label,
    _resolve_sections,
    _section_matches,
)


def test_section_matches_requires_exact_normalized_caption() -> None:
    assert _section_matches("Notes", "Notes") is True
    assert _section_matches("Notes", "notes") is True
    assert _section_matches("Notes and Attachments", "Notes") is False
    assert _section_matches("Notes", "Notes and Attachments") is False


def test_section_matches_prefers_display_value_over_value() -> None:
    assert _section_matches(
        {"display_value": "User Notes", "value": "user_notes"},
        "User Notes",
    ) is True
    # The display_value is used for matching, not the internal value.
    assert _section_matches(
        {"display_value": "User Notes", "value": "admin_notes"},
        "admin_notes",
    ) is False


def test_section_matches_rejects_empty_normalized_values() -> None:
    assert _section_matches("", "Notes") is False
    assert _section_matches("Notes", "") is False
    assert _section_matches("!@#", "Notes") is False


def test_resolve_sections_finds_exact_match() -> None:
    sections = [
        {"sys_id": "s1", "caption": "Notes", "view": "Default view"},
        {"sys_id": "s2", "caption": "Activities", "view": "Default view"},
    ]

    resolved = _resolve_sections(
        sections=sections,
        requested_sections=["Notes"],
        requested_view="Default view",
    )

    assert len(resolved) == 1
    assert resolved[0]["sys_id"] == "s1"


def test_resolve_sections_rejects_prefix_only_match() -> None:
    sections = [
        {"sys_id": "s1", "caption": "Notes and Attachments", "view": "Default view"},
    ]

    with pytest.raises(ValueError, match="form section not found: Notes"):
        _resolve_sections(
            sections=sections,
            requested_sections=["Notes"],
            requested_view="Default view",
        )


def test_resolve_sections_rejects_ambiguous_exact_match() -> None:
    sections = [
        {"sys_id": "s1", "caption": "Notes", "view": "Default view"},
        {"sys_id": "s2", "caption": "Notes", "view": "Default view"},
    ]

    with pytest.raises(ValueError, match="form section match is ambiguous: Notes"):
        _resolve_sections(
            sections=sections,
            requested_sections=["Notes"],
            requested_view="Default view",
        )


def test_normalize_label_strips_non_alphanumeric_and_lowercases() -> None:
    assert _normalize_label("Notes and Attachments") == "notesandattachments"
    assert _normalize_label("User Notes") == "usernotes"
    assert _normalize_label("AI/ML Review") == "aimlreview"
