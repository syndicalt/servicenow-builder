"""Evidence-driven builder maturity scoring for automated handoff routing.

Builder maturity gates whether a generated Update Set candidate is handed off
automatically or routed to manual review. The baseline maturity table below is
the authoritative fallback (the constants previously hardcoded in
``implementation_packet.py``); recorded fulfillment outcomes from the
operational store can adjust it in either direction:

- promotion above the automated handoff threshold must be earned by recorded
  UAT/review outcomes (terminal ``completed`` jobs without rework), and
- regressions in the field (``failed``/``rejected`` jobs or UAT rework
  requests) can demote a surface below the threshold.

Wiring note: ``model_fulfillment`` handlers do not hold an operational store,
so there is no automatic wiring into the fulfillment path. Runtimes that own a
:class:`~jedi_devproject.operational_store.PostgresOperationalStore` should
construct a provider with :func:`maturity_provider_from_operational_store` and
pass it explicitly via the keyword-only ``maturity_provider`` argument of
``build_implementation_packet`` and
``generate_implementation_update_set_candidate_from_packet``.
"""

from __future__ import annotations

from collections.abc import Set as AbstractSet
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.operational_store import SurfaceMaturityEvidenceRecord

BASELINE_BUILDER_MATURITY: dict[str, float] = {
    "table_schema": 0.95,
    "form_layout": 0.95,
    "ui_policies": 0.95,
    "form_sections": 0.30,
    "catalog_definitions": 0.60,
    "catalog_categories": 0.60,
    "employee_center_topics": 0.60,
    "employee_center_connected_content": 0.60,
    # Catalog variable behavior surfaces are new and their customer-update XML
    # shapes are evidence-pending (UAT confirmation required), so they start
    # well below the automated handoff threshold by design.
    "catalog_ui_policies": 0.30,
    "catalog_client_scripts": 0.30,
    # The record producer builder is new and its customer-update XML shapes are
    # evidence-pending (UAT confirmation required), so its candidates route to
    # manual review until recorded outcomes earn promotion.
    "record_producers": 0.30,
    # Attaching an existing fulfillment flow writes the sc_cat_item
    # flow_designer_flow reference, whose retrieved Update Set XML shape is
    # UAT-unconfirmed; candidates that attach a flow route to manual review
    # until recorded outcomes earn promotion.
    "catalog_fulfillment_flows": 0.30,
}
DEFAULT_BUILDER_MATURITY_BASELINE = 0.0
MIN_MATURITY_EVIDENCE_SAMPLES = 5
MATURITY_EVIDENCE_BLEND_PIVOT_SAMPLES = 20
MIN_BUILDER_MATURITY_SCORE = 0.0
MAX_BUILDER_MATURITY_SCORE = 0.99

# The fulfillment-flow attachment surface is exercised through a field on
# sc_cat_item rather than an extra change table, so candidates that attach a
# flow pass it explicitly via ``extra_surfaces``.
CATALOG_FULFILLMENT_FLOW_SURFACE = "catalog_fulfillment_flows"

CHANGE_TABLE_SURFACE_GROUPS: tuple[tuple[frozenset[str], tuple[str, ...]], ...] = (
    (frozenset({"sys_dictionary", "sys_ui_form"}), ("table_schema", "form_layout")),
    (frozenset({"sys_ui_policy", "sys_ui_policy_action"}), ("ui_policies",)),
    (frozenset({"sys_ui_section"}), ("form_sections",)),
    (
        frozenset(
            {
                "sc_cat_item",
                "item_option_new",
                "sc_cat_item_category",
                "m2m_connected_content",
            }
        ),
        (
            "catalog_definitions",
            "catalog_categories",
            "employee_center_topics",
            "employee_center_connected_content",
        ),
    ),
    # Catalog candidates that add variable behavior exercise the behavior
    # surfaces on top of the catalog surfaces; the minimum-score rule then
    # routes them to manual review while those builders stay below threshold.
    (
        frozenset(
            {
                "sc_cat_item",
                "item_option_new",
                "sc_cat_item_category",
                "m2m_connected_content",
                "catalog_ui_policy",
                "catalog_ui_policy_action",
            }
        ),
        (
            "catalog_definitions",
            "catalog_categories",
            "employee_center_topics",
            "employee_center_connected_content",
            "catalog_ui_policies",
        ),
    ),
    (
        frozenset(
            {
                "sc_cat_item",
                "item_option_new",
                "sc_cat_item_category",
                "m2m_connected_content",
                "catalog_script_client",
            }
        ),
        (
            "catalog_definitions",
            "catalog_categories",
            "employee_center_topics",
            "employee_center_connected_content",
            "catalog_client_scripts",
        ),
    ),
    (
        frozenset(
            {
                "sc_cat_item",
                "item_option_new",
                "sc_cat_item_category",
                "m2m_connected_content",
                "catalog_ui_policy",
                "catalog_ui_policy_action",
                "catalog_script_client",
            }
        ),
        (
            "catalog_definitions",
            "catalog_categories",
            "employee_center_topics",
            "employee_center_connected_content",
            "catalog_ui_policies",
            "catalog_client_scripts",
        ),
    ),
    # Record producer candidates exercise the catalog placement surfaces plus
    # the new record_producers surface; the minimum-score rule routes them to
    # manual review while that builder stays below the handoff threshold.
    (
        frozenset(
            {
                "sc_cat_item_producer",
                "item_option_new",
                "sc_cat_item_category",
            }
        ),
        (
            "catalog_definitions",
            "catalog_categories",
            "record_producers",
        ),
    ),
)


class MaturityEvidence(BaseModel):
    """Recorded fulfillment outcome counts for one builder surface."""

    model_config = ConfigDict(extra="forbid")

    surface: str
    samples: int = Field(ge=0)
    successes: int = Field(ge=0)
    failures: int = Field(ge=0)


class BuilderMaturityScore(BaseModel):
    """A maturity score with the provenance reviewers need to audit routing."""

    model_config = ConfigDict(extra="forbid")

    surface: str
    baseline: float
    score: float
    source: Literal["baseline", "evidence_adjusted"]
    evidence_samples: int = 0


class MaturityEvidenceProvider(Protocol):
    def maturity_evidence_for_surface(self, surface: str) -> MaturityEvidence: ...


class SurfaceMaturityEvidenceSource(Protocol):
    """Read-only slice of the operational store used for maturity evidence."""

    def builder_maturity_evidence_for_surface(
        self,
        surface: str,
    ) -> SurfaceMaturityEvidenceRecord: ...


def baseline_builder_maturity_for_surface(surface: str) -> float:
    return BASELINE_BUILDER_MATURITY.get(surface, DEFAULT_BUILDER_MATURITY_BASELINE)


def score_builder_maturity(
    *,
    surface: str,
    evidence: MaturityEvidence | None,
) -> BuilderMaturityScore:
    """Blend the baseline maturity with recorded fulfillment outcome evidence.

    Formula (a sample-size-weighted blend of baseline and observed success
    rate, conservative by construction):

    - ``baseline`` is the authoritative fallback from
      ``BASELINE_BUILDER_MATURITY`` (``0.0`` for unknown surfaces).
    - With no evidence, or fewer than ``MIN_MATURITY_EVIDENCE_SAMPLES``
      samples, the score equals the baseline exactly; maturity changes must be
      earned by recorded outcomes, never by noise from a handful of jobs.
    - With sufficient samples::

          weight   = samples / (samples + MATURITY_EVIDENCE_BLEND_PIVOT_SAMPLES)
          observed = successes / samples              (clamped to [0.0, 1.0])
          score    = (1 - weight) * baseline + weight * observed

      clamped to ``[MIN_BUILDER_MATURITY_SCORE, MAX_BUILDER_MATURITY_SCORE]``
      (``[0.0, 0.99]``).

    The weight grows smoothly with the sample count and never reaches ``1.0``,
    so the baseline always retains influence, and the ``0.99`` ceiling means no
    surface is ever treated as risk-free. More recorded successes raise the
    score monotonically; more recorded failures lower it, which can demote a
    surface below the automated handoff threshold.
    """
    baseline = baseline_builder_maturity_for_surface(surface)
    if evidence is None or evidence.samples < MIN_MATURITY_EVIDENCE_SAMPLES:
        return BuilderMaturityScore(
            surface=surface,
            baseline=baseline,
            score=baseline,
            source="baseline",
            evidence_samples=evidence.samples if evidence is not None else 0,
        )
    weight = evidence.samples / (evidence.samples + MATURITY_EVIDENCE_BLEND_PIVOT_SAMPLES)
    observed = min(1.0, max(0.0, evidence.successes / evidence.samples))
    blended = (1.0 - weight) * baseline + weight * observed
    score = min(MAX_BUILDER_MATURITY_SCORE, max(MIN_BUILDER_MATURITY_SCORE, blended))
    return BuilderMaturityScore(
        surface=surface,
        baseline=baseline,
        score=score,
        source="evidence_adjusted",
        evidence_samples=evidence.samples,
    )


def surfaces_for_change_tables(tables: AbstractSet[str]) -> tuple[str, ...]:
    """Map a candidate's change tables to the builder surfaces they exercise."""
    if not tables:
        return ()
    for group_tables, surfaces in CHANGE_TABLE_SURFACE_GROUPS:
        if tables <= group_tables:
            return surfaces
    return ()


def builder_maturity_for_change_tables(
    tables: AbstractSet[str],
    *,
    provider: MaturityEvidenceProvider | None = None,
    extra_surfaces: tuple[str, ...] = (),
) -> BuilderMaturityScore:
    """Score the builder maturity for a candidate's change tables.

    When the tables map to multiple surfaces the minimum score wins: automated
    handoff is only as mature as the weakest surface it touches. Unmapped
    tables score ``0.0`` and always route to manual review. ``extra_surfaces``
    carries field-level surfaces the change tables alone cannot express (for
    example the sc_cat_item fulfillment-flow reference) and participates in the
    same minimum-score rule.
    """
    surfaces = surfaces_for_change_tables(tables)
    if not surfaces:
        return BuilderMaturityScore(
            surface="unmapped_change_tables",
            baseline=DEFAULT_BUILDER_MATURITY_BASELINE,
            score=DEFAULT_BUILDER_MATURITY_BASELINE,
            source="baseline",
        )
    surfaces = (*surfaces, *extra_surfaces)
    scores = [
        score_builder_maturity(
            surface=surface,
            evidence=(
                provider.maturity_evidence_for_surface(surface) if provider is not None else None
            ),
        )
        for surface in surfaces
    ]
    return min(scores, key=lambda item: item.score)


class OperationalStoreMaturityProvider:
    """Maturity evidence provider backed by operational store aggregates."""

    def __init__(self, store: SurfaceMaturityEvidenceSource) -> None:
        self._store = store

    def maturity_evidence_for_surface(self, surface: str) -> MaturityEvidence:
        record = self._store.builder_maturity_evidence_for_surface(surface)
        return MaturityEvidence(
            surface=record.surface,
            samples=record.samples,
            successes=record.successes,
            failures=record.failures,
        )


def maturity_provider_from_operational_store(
    store: SurfaceMaturityEvidenceSource,
) -> OperationalStoreMaturityProvider:
    """Construct the store-backed provider for explicit wiring.

    The model fulfillment handler does not hold an operational store, so this
    wiring stays explicit: runtimes that own the store call this and pass the
    result to ``build_implementation_packet(..., maturity_provider=...)`` and
    ``generate_implementation_update_set_candidate_from_packet(...,
    maturity_provider=...)``.
    """
    return OperationalStoreMaturityProvider(store)
