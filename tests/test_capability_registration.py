from __future__ import annotations

from jedi_devproject.builder_maturity import (
    BASELINE_BUILDER_MATURITY,
    CATALOG_FULFILLMENT_FLOW_SURFACE,
    CHANGE_TABLE_SURFACE_GROUPS,
    builder_maturity_for_change_tables,
    surfaces_for_change_tables,
)
from jedi_devproject.capabilities import (
    CAPABILITY_REGISTRY,
    Capability,
    generation_capability_profiles,
)
from jedi_devproject.capability_routing import SUPPORTED_BASELINE_CAPABILITIES
from jedi_devproject.implementation_packet import (
    AUTOMATED_HANDOFF_BUILDER_MATURITY_THRESHOLD,
    ImplementationPacket,
    PacketStory,
)
from jedi_devproject.model_fulfillment import CODE_SURFACE_MAP
from jedi_devproject.packet_validation import _expected_tables_for_packet

# Adding a Capability enum member requires wiring it into several separately
# maintained tables (registry, generation profile list, supported baseline set,
# expected-tables map, builder maturity surfaces). Most misses are silent: the
# story routes to the dictionary/form default, model tables go unvalidated, or
# the candidate demotes to manual build with no error. These ledgers make every
# placement explicit so a new member fails loudly here until it is either fully
# wired or consciously added to the matching exemption ledger below.

# Detected by classifiers only to reject or route to manual review; these
# capabilities intentionally have no CapabilityProfile.
INTENT_SIGNAL_ONLY_CAPABILITIES = {
    Capability.CHOICE_VALUES_CREATE,
    Capability.ACL_MODIFY,
    Capability.BUSINESS_RULE_CREATE,
    Capability.SCRIPT_INCLUDE_MODIFY,
    Capability.DATA_MIGRATION,
    Capability.INTEGRATION_MODIFY,
    Capability.UNKNOWN,
}

# Rides the dictionary/form family: supported in baseline routing and mapped to
# the sys_dictionary/sys_ui_form tables, but deliberately has no standalone
# profile (capability_profile() raises KeyError for it).
DICTIONARY_FORM_FAMILY_ALIASES = {Capability.FIELD_LABEL_CREATE}

# Profiled capabilities reachable only through structured automation intent
# (never from free-text baseline routing).
STRUCTURED_INTENT_ONLY_CAPABILITIES = {Capability.FLOW_MODIFY}

# Profiled analysis capabilities excluded from generation_capability_profiles().
CODE_ANALYSIS_PROFILE_CAPABILITIES = {
    Capability.BUSINESS_RULE_ANALYZE,
    Capability.CLIENT_SCRIPT_ANALYZE,
    Capability.SCRIPT_INCLUDE_ANALYZE,
}

# The exact model-output tables allowed per assessed capability. Capabilities
# absent here must yield an empty expected-tables set, which SKIPS table
# validation for their packets - so every buildable capability must be listed.
EXPECTED_MODEL_TABLES: dict[Capability, set[str]] = {
    Capability.CMDB_IRE_GENERATE: {
        "cmdb_identifier",
        "cmdb_identifier_entry",
        "cmdb_reconciliation_definition",
    },
    Capability.UI_POLICY_GENERATE: {"sys_ui_policy", "sys_ui_policy_action"},
    Capability.RECORD_PRODUCER_CREATE: {
        "sc_cat_item_producer",
        "item_option_new",
        "sc_cat_item_category",
    },
    Capability.CATALOG_ITEM_CREATE: {
        "sc_cat_item",
        "item_option_new",
        "sc_cat_item_category",
        "m2m_connected_content",
    },
    Capability.BUSINESS_RULE_GENERATE: {"sys_script"},
    Capability.CLIENT_SCRIPT_GENERATE: {"sys_script_client"},
    Capability.SCRIPT_INCLUDE_GENERATE: {"sys_script_include"},
    Capability.FORM_SECTION_REMOVE: {"sys_ui_section"},
    Capability.DICTIONARY_FIELD_CREATE: {"sys_dictionary", "sys_ui_form"},
    Capability.FORM_LAYOUT_PLACE_FIELD: {"sys_dictionary", "sys_ui_form"},
    Capability.FIELD_LABEL_CREATE: {"sys_dictionary", "sys_ui_form"},
}

# Buildable capabilities whose expected tables have no CHANGE_TABLE_SURFACE_GROUPS
# entry. Their candidates score the 0.0 unmapped default and always route to
# manual review; evidence can never promote them until a surface mapping exists.
SURFACE_UNMAPPED_CAPABILITIES = {
    Capability.BUSINESS_RULE_GENERATE,
    Capability.CLIENT_SCRIPT_GENERATE,
    Capability.SCRIPT_INCLUDE_GENERATE,
    Capability.CMDB_IRE_GENERATE,
}


def _packet(*, capabilities: list[Capability]) -> ImplementationPacket:
    return ImplementationPacket(
        task="implementation_candidate",
        provider_id="registration_check_provider",
        story=PacketStory(
            number="STRY0000",
            short_description="registration self-check",
            description="registration self-check",
            story_points=2.0,
            priority=3,
            state="ready",
        ),
        safety_decision="automated_build",
        safety_reasons=["registration self-check"],
        risk_score=0.1,
        allowed_tables=[],
        allowed_operations=[],
        capability_assessment={
            "capabilities": [capability.value for capability in capabilities]
        },
        context_sections={},
        retrieval_citations=[],
        output_contract={},
    )


def test_every_capability_is_placed_in_exactly_one_wiring_ledger() -> None:
    registered = set(CAPABILITY_REGISTRY)
    ledgers = [
        registered,
        INTENT_SIGNAL_ONLY_CAPABILITIES,
        DICTIONARY_FORM_FAMILY_ALIASES,
    ]
    placed: set[Capability] = set()
    for ledger in ledgers:
        assert not placed & ledger
        placed |= ledger
    assert placed == set(Capability)


def test_registry_profiles_bind_their_own_capability() -> None:
    for capability, profile in CAPABILITY_REGISTRY.items():
        assert profile.capability == capability


def test_generation_profiles_are_registry_minus_code_analysis_profiles() -> None:
    generation = [profile.capability for profile in generation_capability_profiles()]
    assert len(generation) == len(set(generation))
    assert set(generation) == set(CAPABILITY_REGISTRY) - CODE_ANALYSIS_PROFILE_CAPABILITIES


def test_supported_baseline_matches_registry_and_documented_exemptions() -> None:
    expected = (
        set(CAPABILITY_REGISTRY) - STRUCTURED_INTENT_ONLY_CAPABILITIES
    ) | DICTIONARY_FORM_FAMILY_ALIASES
    assert expected == SUPPORTED_BASELINE_CAPABILITIES


def test_expected_model_tables_pinned_for_every_capability() -> None:
    for capability in Capability:
        expected = EXPECTED_MODEL_TABLES.get(capability, set())
        actual = _expected_tables_for_packet(_packet(capabilities=[capability]))
        assert actual == expected, capability
    validated = {
        capability for capability in Capability if EXPECTED_MODEL_TABLES.get(capability)
    }
    buildable = set(EXPECTED_MODEL_TABLES)
    assert validated == buildable


def test_catalog_behavior_capabilities_extend_catalog_item_expected_tables() -> None:
    with_ui_policy = _expected_tables_for_packet(
        _packet(
            capabilities=[
                Capability.CATALOG_ITEM_CREATE,
                Capability.CATALOG_UI_POLICY_GENERATE,
            ]
        )
    )
    assert with_ui_policy == EXPECTED_MODEL_TABLES[Capability.CATALOG_ITEM_CREATE] | {
        "catalog_ui_policy",
        "catalog_ui_policy_action",
    }
    with_client_script = _expected_tables_for_packet(
        _packet(
            capabilities=[
                Capability.CATALOG_ITEM_CREATE,
                Capability.CATALOG_CLIENT_SCRIPT_GENERATE,
            ]
        )
    )
    assert with_client_script == EXPECTED_MODEL_TABLES[Capability.CATALOG_ITEM_CREATE] | {
        "catalog_script_client"
    }
    with_both = _expected_tables_for_packet(
        _packet(
            capabilities=[
                Capability.CATALOG_ITEM_CREATE,
                Capability.CATALOG_UI_POLICY_GENERATE,
                Capability.CATALOG_CLIENT_SCRIPT_GENERATE,
            ]
        )
    )
    assert with_both == with_ui_policy | with_client_script


def test_expected_tables_map_to_explicitly_scored_builder_surfaces() -> None:
    for capability, tables in EXPECTED_MODEL_TABLES.items():
        surfaces = surfaces_for_change_tables(tables)
        if capability in SURFACE_UNMAPPED_CAPABILITIES:
            assert surfaces == (), capability
            score = builder_maturity_for_change_tables(tables)
            assert score.surface == "unmapped_change_tables"
            assert score.score == 0.0
            continue
        assert surfaces, capability
        for surface in surfaces:
            assert surface in BASELINE_BUILDER_MATURITY, (capability, surface)


def test_surface_group_names_all_have_explicit_baselines() -> None:
    group_surfaces = {
        surface for _tables, surfaces in CHANGE_TABLE_SURFACE_GROUPS for surface in surfaces
    }
    assert group_surfaces <= set(BASELINE_BUILDER_MATURITY)
    assert CATALOG_FULFILLMENT_FLOW_SURFACE in BASELINE_BUILDER_MATURITY


def test_mature_surfaces_match_deterministic_handoff_dispatch() -> None:
    mature = {
        surface
        for surface, baseline in BASELINE_BUILDER_MATURITY.items()
        if baseline >= AUTOMATED_HANDOFF_BUILDER_MATURITY_THRESHOLD
    }
    # update_set_handoff._customer_updates_for_candidate dispatches exactly the
    # dictionary/form and ui-policy table sets; those are the only surfaces at
    # or above the automated handoff threshold. Promoting a surface past the
    # threshold without adding a deterministic handoff builder (or vice versa)
    # must be a conscious change to both this ledger and that dispatch.
    assert mature == {"table_schema", "form_layout", "ui_policies"}


def test_code_surface_map_covers_exactly_the_code_analysis_profiles() -> None:
    assert set(CODE_SURFACE_MAP) == CODE_ANALYSIS_PROFILE_CAPABILITIES
    for capability, (surface, source_table) in CODE_SURFACE_MAP.items():
        profile = CAPABILITY_REGISTRY[capability]
        assert source_table in profile.supported_artifacts, (capability, surface)
