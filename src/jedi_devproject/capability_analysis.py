"""Facade for story capability analysis.

The implementation is split across:

- :mod:`jedi_devproject.story_features` — story text normalization and feature extraction
- :mod:`jedi_devproject.intent_classifier` — story text to requested-capability classification
- :mod:`jedi_devproject.capability_assessment` — assessment construction and operator feedback
- :mod:`jedi_devproject.capability_routing` — automation-outcome routing

This module re-exports the public API so existing imports keep working.
"""

from __future__ import annotations

from jedi_devproject.capability_assessment import (
    CURRENT_AUTOMATION_MAX_POINTS,
    FULL_MATURITY_MAX_AUTOMATED_POINTS,
)
from jedi_devproject.capability_routing import (
    AUTOMATED_INTENT_REASONS,
    SUPPORTED_BASELINE_CAPABILITIES,
    analyze_story_capabilities,
)

__all__ = [
    "AUTOMATED_INTENT_REASONS",
    "CURRENT_AUTOMATION_MAX_POINTS",
    "FULL_MATURITY_MAX_AUTOMATED_POINTS",
    "SUPPORTED_BASELINE_CAPABILITIES",
    "analyze_story_capabilities",
]
