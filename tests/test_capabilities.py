from jedi_devproject.capabilities import (
    Capability,
    FieldFormIntent,
    StoryCapabilityAssessment,
    SuitabilityOutcome,
)


def test_field_form_intent_derives_custom_field_name_from_label() -> None:
    intent = FieldFormIntent(
        target_table="incident",
        field_label="Antics",
        field_type="string",
        max_length=4000,
        placement_anchor="description",
        placement_position="below",
    )

    assert intent.field_name == "u_antics"


def test_assessment_for_supported_dictionary_form_is_automated() -> None:
    assessment = StoryCapabilityAssessment(
        story_number="STRY0010001",
        outcome=SuitabilityOutcome.AUTOMATED_BUILD,
        capabilities={
            Capability.DICTIONARY_FIELD_CREATE,
            Capability.FIELD_LABEL_CREATE,
            Capability.FORM_LAYOUT_PLACE_FIELD,
        },
        supported_capabilities={
            Capability.DICTIONARY_FIELD_CREATE,
            Capability.FIELD_LABEL_CREATE,
            Capability.FORM_LAYOUT_PLACE_FIELD,
        },
        intent=FieldFormIntent(
            target_table="incident",
            field_label="Antics",
            field_type="string",
            max_length=4000,
            placement_anchor="description",
            placement_position="below",
        ),
        reasons=["supported low-complexity dictionary/form request"],
        missing_details=[],
        unsupported_capabilities=set(),
        risk_score=0.18,
        confidence=0.82,
    )

    assert assessment.is_automated
    assert assessment.intent is not None
    assert assessment.intent.field_name == "u_antics"
    assert assessment.unsupported_capabilities == set()


def test_assessment_reports_unsupported_capability() -> None:
    assessment = StoryCapabilityAssessment(
        story_number="STRY0099999",
        outcome=SuitabilityOutcome.UNSUPPORTED_CAPABILITY,
        capabilities={Capability.FLOW_MODIFY},
        supported_capabilities={Capability.DICTIONARY_FIELD_CREATE},
        intent=None,
        reasons=["Flow Designer changes are not supported by this pipeline"],
        missing_details=[],
        unsupported_capabilities={Capability.FLOW_MODIFY},
        risk_score=0.65,
        confidence=0.7,
    )

    assert not assessment.is_automated
    assert assessment.unsupported_capability_names == ["flow_modify"]
