from __future__ import annotations

import math

from jedi_devproject.builder_maturity import (
    BASELINE_BUILDER_MATURITY,
    CATALOG_FULFILLMENT_FLOW_SURFACE,
    MATURITY_EVIDENCE_BLEND_PIVOT_SAMPLES,
    MAX_BUILDER_MATURITY_SCORE,
    MIN_MATURITY_EVIDENCE_SAMPLES,
    MaturityEvidence,
    OperationalStoreMaturityProvider,
    baseline_builder_maturity_for_surface,
    builder_maturity_for_change_tables,
    maturity_provider_from_operational_store,
    score_builder_maturity,
    surfaces_for_change_tables,
)
from jedi_devproject.operational_store import SurfaceMaturityEvidenceRecord


def _evidence(
    surface: str,
    *,
    samples: int,
    successes: int,
    failures: int | None = None,
) -> MaturityEvidence:
    return MaturityEvidence(
        surface=surface,
        samples=samples,
        successes=successes,
        failures=failures if failures is not None else samples - successes,
    )


class StubMaturityProvider:
    def __init__(self, evidence_by_surface: dict[str, MaturityEvidence]) -> None:
        self.evidence_by_surface = evidence_by_surface
        self.requested: list[str] = []

    def maturity_evidence_for_surface(self, surface: str) -> MaturityEvidence:
        self.requested.append(surface)
        return self.evidence_by_surface.get(
            surface,
            MaturityEvidence(surface=surface, samples=0, successes=0, failures=0),
        )


class FakeEvidenceStore:
    def __init__(self, record: SurfaceMaturityEvidenceRecord) -> None:
        self.record = record
        self.requested: list[str] = []

    def builder_maturity_evidence_for_surface(
        self,
        surface: str,
    ) -> SurfaceMaturityEvidenceRecord:
        self.requested.append(surface)
        return self.record


def test_baseline_table_preserves_authoritative_constants() -> None:
    assert baseline_builder_maturity_for_surface("table_schema") == 0.95
    assert baseline_builder_maturity_for_surface("form_layout") == 0.95
    assert baseline_builder_maturity_for_surface("ui_policies") == 0.95
    assert baseline_builder_maturity_for_surface("form_sections") == 0.30
    assert baseline_builder_maturity_for_surface("catalog_definitions") == 0.60
    assert baseline_builder_maturity_for_surface("catalog_categories") == 0.60
    assert baseline_builder_maturity_for_surface("employee_center_topics") == 0.60
    assert baseline_builder_maturity_for_surface("employee_center_connected_content") == 0.60
    assert baseline_builder_maturity_for_surface("catalog_ui_policies") == 0.30
    assert baseline_builder_maturity_for_surface("catalog_client_scripts") == 0.30
    assert baseline_builder_maturity_for_surface("record_producers") == 0.30
    assert baseline_builder_maturity_for_surface("catalog_fulfillment_flows") == 0.30
    assert baseline_builder_maturity_for_surface("flows") == 0.0
    assert set(BASELINE_BUILDER_MATURITY) == {
        "table_schema",
        "form_layout",
        "ui_policies",
        "form_sections",
        "catalog_definitions",
        "catalog_categories",
        "employee_center_topics",
        "employee_center_connected_content",
        "catalog_ui_policies",
        "catalog_client_scripts",
        "record_producers",
        "catalog_fulfillment_flows",
    }


def test_score_without_evidence_equals_baseline_exactly() -> None:
    scored = score_builder_maturity(surface="form_sections", evidence=None)

    assert scored.score == 0.30
    assert scored.baseline == 0.30
    assert scored.source == "baseline"
    assert scored.evidence_samples == 0


def test_score_below_minimum_samples_equals_baseline_exactly() -> None:
    samples = MIN_MATURITY_EVIDENCE_SAMPLES - 1

    scored = score_builder_maturity(
        surface="form_sections",
        evidence=_evidence("form_sections", samples=samples, successes=samples),
    )

    assert scored.score == 0.30
    assert scored.source == "baseline"
    assert scored.evidence_samples == samples


def test_score_at_minimum_samples_is_evidence_adjusted() -> None:
    samples = MIN_MATURITY_EVIDENCE_SAMPLES

    scored = score_builder_maturity(
        surface="catalog_definitions",
        evidence=_evidence("catalog_definitions", samples=samples, successes=samples),
    )

    weight = samples / (samples + MATURITY_EVIDENCE_BLEND_PIVOT_SAMPLES)
    expected = (1.0 - weight) * 0.60 + weight * 1.0
    assert scored.source == "evidence_adjusted"
    assert scored.evidence_samples == samples
    assert math.isclose(scored.score, expected)
    assert scored.score > scored.baseline


def test_score_is_monotonic_in_successes_and_failures() -> None:
    surface = "catalog_definitions"
    mostly_failing = score_builder_maturity(
        surface=surface,
        evidence=_evidence(surface, samples=20, successes=5),
    )
    balanced = score_builder_maturity(
        surface=surface,
        evidence=_evidence(surface, samples=20, successes=10),
    )
    mostly_passing = score_builder_maturity(
        surface=surface,
        evidence=_evidence(surface, samples=20, successes=18),
    )

    assert mostly_failing.score < balanced.score < mostly_passing.score
    assert mostly_failing.score < mostly_failing.baseline
    assert mostly_passing.score > mostly_passing.baseline


def test_score_is_clamped_to_ceiling_and_floor() -> None:
    promoted = score_builder_maturity(
        surface="table_schema",
        evidence=_evidence("table_schema", samples=10_000, successes=10_000),
    )
    demoted = score_builder_maturity(
        surface="form_sections",
        evidence=_evidence("form_sections", samples=10_000, successes=0),
    )

    assert promoted.score == MAX_BUILDER_MATURITY_SCORE
    assert 0.0 <= demoted.score < 0.30


def test_score_clamps_inconsistent_observed_success_rate() -> None:
    scored = score_builder_maturity(
        surface="table_schema",
        evidence=_evidence("table_schema", samples=10, successes=20, failures=0),
    )

    assert scored.score <= MAX_BUILDER_MATURITY_SCORE
    weight = 10 / (10 + MATURITY_EVIDENCE_BLEND_PIVOT_SAMPLES)
    assert math.isclose(scored.score, (1.0 - weight) * 0.95 + weight * 1.0)


def test_surfaces_for_change_tables_maps_known_table_groups() -> None:
    assert surfaces_for_change_tables({"sys_dictionary", "sys_ui_form"}) == (
        "table_schema",
        "form_layout",
    )
    assert surfaces_for_change_tables({"sys_dictionary"}) == ("table_schema", "form_layout")
    assert surfaces_for_change_tables({"sys_ui_policy", "sys_ui_policy_action"}) == (
        "ui_policies",
    )
    assert surfaces_for_change_tables({"sys_ui_section"}) == ("form_sections",)
    assert surfaces_for_change_tables(
        {"sc_cat_item", "item_option_new", "sc_cat_item_category", "m2m_connected_content"}
    ) == (
        "catalog_definitions",
        "catalog_categories",
        "employee_center_topics",
        "employee_center_connected_content",
    )
    assert surfaces_for_change_tables({"sys_script"}) == ()
    assert surfaces_for_change_tables(set()) == ()


def test_builder_maturity_for_change_tables_baseline_matches_legacy_constants() -> None:
    assert builder_maturity_for_change_tables({"sys_dictionary", "sys_ui_form"}).score == 0.95
    assert builder_maturity_for_change_tables({"sys_ui_policy"}).score == 0.95
    assert builder_maturity_for_change_tables({"sys_ui_section"}).score == 0.30
    assert builder_maturity_for_change_tables({"sc_cat_item", "item_option_new"}).score == 0.60
    assert builder_maturity_for_change_tables({"sys_script"}).score == 0.0
    assert builder_maturity_for_change_tables(set()).score == 0.0
    assert builder_maturity_for_change_tables(set()).source == "baseline"


def test_builder_maturity_for_change_tables_takes_conservative_minimum() -> None:
    provider = StubMaturityProvider(
        {
            "table_schema": _evidence("table_schema", samples=40, successes=40),
            "form_layout": _evidence("form_layout", samples=40, successes=4),
        }
    )

    scored = builder_maturity_for_change_tables(
        {"sys_dictionary", "sys_ui_form"},
        provider=provider,
    )

    assert provider.requested == ["table_schema", "form_layout"]
    assert scored.surface == "form_layout"
    assert scored.source == "evidence_adjusted"
    assert scored.score < 0.95


def test_fulfillment_flow_extra_surface_takes_conservative_minimum() -> None:
    catalog_tables = {
        "sc_cat_item",
        "item_option_new",
        "sc_cat_item_category",
        "m2m_connected_content",
    }

    without_flow = builder_maturity_for_change_tables(catalog_tables)
    with_flow = builder_maturity_for_change_tables(
        catalog_tables,
        extra_surfaces=(CATALOG_FULFILLMENT_FLOW_SURFACE,),
    )

    assert without_flow.score == 0.60
    assert with_flow.surface == "catalog_fulfillment_flows"
    assert with_flow.score == 0.30
    assert with_flow.source == "baseline"


def test_extra_surfaces_do_not_rescue_unmapped_change_tables() -> None:
    scored = builder_maturity_for_change_tables(
        {"sys_script"},
        extra_surfaces=(CATALOG_FULFILLMENT_FLOW_SURFACE,),
    )

    assert scored.surface == "unmapped_change_tables"
    assert scored.score == 0.0


def test_operational_store_provider_converts_store_record_to_evidence() -> None:
    store = FakeEvidenceStore(
        SurfaceMaturityEvidenceRecord(
            surface="form_sections",
            samples=12,
            successes=9,
            failures=3,
        )
    )
    provider = maturity_provider_from_operational_store(store)

    evidence = provider.maturity_evidence_for_surface("form_sections")

    assert isinstance(provider, OperationalStoreMaturityProvider)
    assert store.requested == ["form_sections"]
    assert evidence == MaturityEvidence(
        surface="form_sections",
        samples=12,
        successes=9,
        failures=3,
    )


_CATALOG_ITEM_TABLES = frozenset(
    {"sc_cat_item", "item_option_new", "sc_cat_item_category", "m2m_connected_content"}
)
_CATALOG_SURFACES = (
    "catalog_definitions",
    "catalog_categories",
    "employee_center_topics",
    "employee_center_connected_content",
)


def test_catalog_behavior_tables_map_to_behavior_surfaces() -> None:
    assert surfaces_for_change_tables(set(_CATALOG_ITEM_TABLES)) == _CATALOG_SURFACES
    assert surfaces_for_change_tables(
        _CATALOG_ITEM_TABLES | {"catalog_ui_policy", "catalog_ui_policy_action"}
    ) == (*_CATALOG_SURFACES, "catalog_ui_policies")
    assert surfaces_for_change_tables(
        _CATALOG_ITEM_TABLES | {"catalog_script_client"}
    ) == (*_CATALOG_SURFACES, "catalog_client_scripts")
    assert surfaces_for_change_tables(
        _CATALOG_ITEM_TABLES
        | {"catalog_ui_policy", "catalog_ui_policy_action", "catalog_script_client"}
    ) == (*_CATALOG_SURFACES, "catalog_ui_policies", "catalog_client_scripts")


def test_catalog_behavior_tables_score_at_conservative_baseline() -> None:
    scored = builder_maturity_for_change_tables(
        _CATALOG_ITEM_TABLES
        | {"catalog_ui_policy", "catalog_ui_policy_action", "catalog_script_client"}
    )

    assert scored.score == 0.30
    assert scored.source == "baseline"
    assert scored.surface in {"catalog_ui_policies", "catalog_client_scripts"}


def test_record_producer_change_tables_map_to_record_producer_surfaces() -> None:
    surfaces = surfaces_for_change_tables(
        {"sc_cat_item_producer", "item_option_new", "sc_cat_item_category"}
    )

    assert surfaces == (
        "catalog_definitions",
        "catalog_categories",
        "record_producers",
    )


def test_record_producer_candidates_score_at_conservative_baseline() -> None:
    scored = builder_maturity_for_change_tables(
        {"sc_cat_item_producer", "item_option_new", "sc_cat_item_category"}
    )

    assert scored.surface == "record_producers"
    assert scored.score == 0.30
    assert scored.source == "baseline"


def test_catalog_change_tables_keep_their_existing_surface_mapping() -> None:
    surfaces = surfaces_for_change_tables(
        {
            "sc_cat_item",
            "item_option_new",
            "sc_cat_item_category",
            "m2m_connected_content",
        }
    )

    assert surfaces == (
        "catalog_definitions",
        "catalog_categories",
        "employee_center_topics",
        "employee_center_connected_content",
    )
